"""
AI Ayurvedic Health Assessment Platform
Run: streamlit run main.py
"""

import os
import sys
from pathlib import Path

# Ensure local packages resolve first
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from dotenv import load_dotenv

_APP_DIR = Path(__file__).parent
load_dotenv(_APP_DIR / ".env")
load_dotenv(_APP_DIR / ".env.example")  # fallback if .env absent

from components.assessment_form import render_assessment_form
from components.output_page import render_output_page
from components.recommendation_engine import RecommendationEngine
from components.retrieval import VectorDB

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

COLLECTION_PATHS = {
    "dosha":     DATA_DIR / "dosha_documents",
    "diet":      DATA_DIR / "diet_documents",
    "product":   DATA_DIR / "product_documents",
    "medical":   DATA_DIR / "medical_documents",
    "lifestyle": DATA_DIR / "lifestyle_documents",
}

ALLOWED_TYPES = ["pdf", "docx", "txt"]

COLLECTION_LABELS = {
    "dosha":     "Dosha / Constitution Documents",
    "diet":      "Diet Chart Documents",
    "product":   "Product Catalogue Documents",
    "medical":   "Medical Reference Documents",
    "lifestyle": "Lifestyle Guide Documents",
}


# ---------------------------------------------------------------------------
# Auto-index bundled diet documents (no user upload required)
# ---------------------------------------------------------------------------
def _auto_index_diet(db: "VectorDB") -> None:
    """Index diet chart documents automatically if not already indexed."""
    if db.get_chunk_count("diet") > 0:
        return  # already indexed
    diet_folder = COLLECTION_PATHS["diet"]
    has_docs = any(
        f.suffix.lower() in {".pdf", ".docx", ".txt"}
        for f in diet_folder.iterdir()
        if f.name != "_index.json"
    ) if diet_folder.exists() else False
    if has_docs:
        db.ingest_collection("diet")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init():
    if "page" not in st.session_state:
        st.session_state.page = "form"
    if "results" not in st.session_state:
        st.session_state.results = None
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "db" not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY", "")
        st.session_state.db = VectorDB(COLLECTION_PATHS, api_key=api_key)
        # Auto-index diet documents if not yet indexed
        _auto_index_diet(st.session_state.db)
    if "last_prompts" not in st.session_state:
        st.session_state.last_prompts = {}
    if "diet_indexed" not in st.session_state:
        st.session_state.diet_indexed = st.session_state.db.get_chunk_count("diet") > 0


# ---------------------------------------------------------------------------
# Sidebar — document upload and indexing
# ---------------------------------------------------------------------------
def _render_sidebar():
    db: VectorDB = st.session_state.db

    with st.sidebar:
        st.header("📚 Document Collections")
        st.caption(
            "Upload approved documents to each collection. "
            "The AI uses **only** these documents — no outside knowledge."
        )
        st.divider()

        # Diet is auto-managed — show status but no upload UI
        diet_count = db.get_chunk_count("diet")
        if diet_count > 0:
            st.success(f"✅ Diet charts auto-indexed ({diet_count} chunks)")
        else:
            st.warning("⚠️ Diet charts not yet indexed — restart the app.")

        st.divider()

        # User-managed collections (all except diet)
        USER_COLLECTIONS = {k: v for k, v in COLLECTION_PATHS.items() if k != "diet"}
        for col_name, col_path in USER_COLLECTIONS.items():
            label = COLLECTION_LABELS[col_name]
            chunk_count = db.get_chunk_count(col_name)
            status = f"✅ {chunk_count} chunks" if chunk_count > 0 else "⚠️ Not indexed"

            with st.expander(f"{label} — {status}"):
                # Existing files
                col_path.mkdir(parents=True, exist_ok=True)
                existing = [
                    f for f in col_path.iterdir()
                    if f.suffix.lower() in {".pdf", ".docx", ".txt"}
                ]
                if existing:
                    st.caption(f"Files in library: {', '.join(f.name for f in existing)}")

                # Upload
                files = st.file_uploader(
                    f"Add files to {col_name}",
                    type=ALLOWED_TYPES,
                    accept_multiple_files=True,
                    key=f"upload_{col_name}",
                    label_visibility="collapsed",
                )
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(
                        "Save & Index",
                        key=f"idx_{col_name}",
                        disabled=not files,
                        use_container_width=True,
                    ):
                        for f in files:
                            dest = col_path / f.name
                            dest.write_bytes(f.getvalue())
                        with st.spinner(f"Indexing {col_name}…"):
                            n = db.ingest_collection(col_name)
                        st.success(f"Indexed {n} chunks")
                        st.rerun()
                with col_b:
                    if st.button(
                        "Re-index",
                        key=f"reindex_{col_name}",
                        disabled=not existing,
                        use_container_width=True,
                    ):
                        with st.spinner(f"Re-indexing {col_name}…"):
                            n = db.ingest_collection(col_name)
                        st.success(f"Re-indexed {n} chunks")
                        st.rerun()

        st.divider()
        total = sum(db.get_chunk_count(n) for n in COLLECTION_PATHS)
        st.metric("Total indexed chunks", total)
        if total == 0:
            st.warning("No documents indexed. Upload documents above before generating a report.")

        # ── LLM Prompt Preview (shown only after a report is generated) ──
        prompts = st.session_state.get("last_prompts", {})
        if prompts:
            st.divider()
            st.markdown(
                '<div style="font-size:0.78rem;font-weight:700;color:#3730a3;'
                'text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">'
                'LLM Prompts Used</div>',
                unsafe_allow_html=True,
            )
            PROMPT_LABELS = {
                "summary": "Opening Summary",
                "dosha":   "Dosha Analysis",
                "diet":    "Diet Recommendations",
                "product": "Product Recommendations",
            }
            for key, label in PROMPT_LABELS.items():
                p = prompts.get(key)
                if not p:
                    continue
                with st.expander(label):
                    st.markdown("**System prompt**")
                    st.code(p["system"], language="text")
                    st.markdown("**User prompt**")
                    st.code(p["user"], language="text")


# ---------------------------------------------------------------------------
# Assessment → report flow
# ---------------------------------------------------------------------------
def _run_assessment(profile: dict) -> dict:
    db: VectorDB = st.session_state.db
    engine = RecommendationEngine(api_key=os.getenv("OPENAI_API_KEY", ""))

    progress = st.progress(0, text="Retrieving dosha documents…")

    dosha_chunks    = db.retrieve_for_dosha(profile)
    progress.progress(20, text="Retrieving diet documents…")

    diet_chunks     = db.retrieve_for_diet(profile)
    medical_chunks  = db.retrieve_for_medical(profile)
    progress.progress(40, text="Retrieving product documents…")

    # Retrieve ALL product chunks (small collection — grab everything)
    product_chunks   = db.retrieve_for_products(profile, top_k=20)
    lifestyle_chunks = db.retrieve_for_lifestyle(profile)
    progress.progress(60, text="Analysing dosha constitution…")

    dosha_result    = engine.analyze_dosha(profile, dosha_chunks)
    progress.progress(65, text="Generating diet recommendations…")

    diet_result     = engine.get_diet_recommendations(
        profile, diet_chunks + medical_chunks + lifestyle_chunks
    )
    progress.progress(80, text="Generating product recommendations…")

    product_result  = engine.get_product_recommendations(
        profile, product_chunks + medical_chunks
    )
    progress.progress(93, text="Writing your personal summary…")

    opening_summary = engine.generate_opening_summary(profile, dosha_result)
    progress.progress(100, text="Done!")
    progress.empty()

    # Persist prompts for sidebar preview
    st.session_state.last_prompts = engine.last_prompts

    return {
        "opening_summary": opening_summary,
        "dosha":           dosha_result,
        "diet":            diet_result,
        "product":         product_result,
        "chunks": {
            "dosha":   dosha_chunks,
            "diet":    diet_chunks,
            "product": product_chunks,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Ayurvedic Health Assessment",
        page_icon="🌿",
        layout="wide",
    )

    _init()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        st.error(
            "**OPENAI_API_KEY** is not set. "
            "Create a `.env` file in the `strengthiva/` folder with:\n\n"
            "```\nOPENAI_API_KEY=sk-...\n```"
        )
        st.stop()

    # Inject global CSS on every page
    from components.output_page import GLOBAL_CSS
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    _render_sidebar()

    # ------------------------------------------------------------------ Form
    if st.session_state.page == "form":
        st.markdown(
            '<div style="font-size:2rem;font-weight:800;color:#3730a3;margin-bottom:6px;">🌿 Ayurvedic Health Assessment</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color:#475569;font-size:0.92rem;margin-bottom:24px;">'
            'Complete the assessment below. Your personalised report will be generated '
            'exclusively from approved Ayurvedic documents — grounded, reliable, zero hallucination.'
            '</div>',
            unsafe_allow_html=True,
        )

        profile = render_assessment_form()

        if profile is not None:
            st.session_state.profile = profile
            results = _run_assessment(profile)
            st.session_state.results = results
            st.session_state.page = "results"
            st.rerun()

    # ------------------------------------------------------------------ Results
    elif st.session_state.page == "results":
        def _do_refresh():
            with st.spinner("Regenerating your report…"):
                results = _run_assessment(st.session_state.profile)
            st.session_state.results = results
            st.rerun()

        col_back, _ = st.columns([1, 6])
        with col_back:
            if st.button("New Assessment"):
                st.session_state.page = "form"
                st.session_state.results = None
                st.session_state.profile = None
                st.rerun()

        render_output_page(
            results=st.session_state.results,
            profile=st.session_state.profile,
            on_refresh=_do_refresh,
        )


if __name__ == "__main__":
    main()
