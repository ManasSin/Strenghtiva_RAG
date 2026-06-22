"""
Output page — native Streamlit base, targeted inline styling only.
No global CSS overrides. Cosmetic-only improvements per section.
"""

import json
import re as _re
from datetime import date
from typing import Any, Callable, Dict, Optional

import streamlit as st

DAYS      = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MEAL_SLOTS = [
    ("breakfast",   "Breakfast",   "7:30 AM",  "#f59e0b"),   # amber
    ("mid_morning", "Mid-Morning", "10:30 AM", "#10b981"),   # emerald
    ("lunch",       "Lunch",       "1:00 PM",  "#3b82f6"),   # blue
    ("evening",     "Evening",     "4:30 PM",  "#8b5cf6"),   # violet
    ("dinner",      "Dinner",      "7:30 PM",  "#6366f1"),   # indigo
]
MEAL_ICONS = {
    "breakfast":   "☀️",
    "mid_morning": "🍎",
    "lunch":       "🍽️",
    "evening":     "🌤️",
    "dinner":      "🌙",
}

# Empty — no global CSS
GLOBAL_CSS = ""
WATERMARK_HTML = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _card(content_html: str, bg: str = "#f8fafc", border_color: str = "#e2e8f0",
          border_left: str = "", padding: str = "16px 20px", radius: str = "10px") -> str:
    left = f"border-left: 4px solid {border_left};" if border_left else ""
    return (
        f'<div style="background:{bg};border:1px solid {border_color};'
        f'{left}border-radius:{radius};padding:{padding};margin-bottom:10px;">'
        f'{content_html}</div>'
    )


def _pill(text: str, bg: str, color: str) -> str:
    return (
        f'<span style="background:{bg};color:{color};border-radius:20px;'
        f'padding:3px 12px;font-size:0.78rem;font-weight:600;'
        f'display:inline-block;margin:3px 4px 3px 0;">{text}</span>'
    )


def _section_label(text: str, color: str = "#64748b") -> None:
    st.markdown(
        f'<p style="font-size:0.72rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.08em;color:{color};margin:14px 0 6px 0;">{text}</p>',
        unsafe_allow_html=True,
    )


def _split_meal(raw: str):
    return [x.strip().rstrip(".") for x in _re.split(r"[,;]| and ", raw) if x.strip()]


# ---------------------------------------------------------------------------
# Section 0 — Opening + Metric tiles
# ---------------------------------------------------------------------------
def _render_opening(summary: str, profile: Dict) -> None:
    name = profile.get("name", "Friend")

    # Highlighted summary banner
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#3730a3,#4f46e5);'
        f'border-radius:14px;padding:24px 28px;margin-bottom:20px;">'
        f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.1em;color:rgba(255,255,255,0.55);margin-bottom:8px;">'
        f'Personalised Assessment — {name}</div>'
        f'<div style="font-size:1.0rem;line-height:1.7;color:#fff;font-weight:500;">'
        f'{summary}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Metric tiles — 6 columns, each a small card
    bmi    = profile.get("bmi", 0)
    sleep  = profile.get("sleep_hours", 0)
    stress = profile.get("stress_level", "—")
    energy = profile.get("energy_level", "—")
    water  = profile.get("water_intake_liters", "—")
    age    = profile.get("age", "—")

    def _color_bmi(v):
        if 18.5 <= v <= 24.9: return "#059669"
        if v > 30: return "#dc2626"
        return "#d97706"

    def _color_stress(s):
        if "High" in s: return "#dc2626"
        if "Low" in s: return "#059669"
        return "#0284c7"

    def _color_sleep(h):
        if h >= 7: return "#059669"
        if h < 6: return "#dc2626"
        return "#d97706"

    tiles = [
        ("Age",       str(age),          "#6366f1", "yrs"),
        ("BMI",       str(bmi),          _color_bmi(bmi),      ""),
        ("Sleep",     f"{sleep}",        _color_sleep(sleep),  "hrs"),
        ("Stress",    stress,            _color_stress(stress), ""),
        ("Energy",    energy,            "#0284c7",             ""),
        ("Hydration", f"{water}",        "#0284c7",             "L/day"),
    ]

    cols = st.columns(6)
    for col, (label, val, color, unit) in zip(cols, tiles):
        with col:
            st.markdown(
                f'<div style="background:#fff;border:1px solid #e2e8f0;border-top:3px solid {color};'
                f'border-radius:10px;padding:12px 10px;text-align:center;">'
                f'<div style="font-size:1.25rem;font-weight:800;color:{color};">{val}'
                f'<span style="font-size:0.65rem;color:#94a3b8;font-weight:500;margin-left:2px;">{unit}</span></div>'
                f'<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:.07em;'
                f'color:#94a3b8;margin-top:3px;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Section 1 — Dosha (collapsible after title)
# ---------------------------------------------------------------------------
def _render_dosha(dosha: Dict) -> None:
    st.markdown(
        '<div style="background:#f5f3ff;border-left:4px solid #7c3aed;'
        'border-radius:0 10px 10px 0;padding:10px 16px;margin-bottom:4px;">'
        '<span style="font-size:1.05rem;font-weight:700;color:#5b21b6;">Dosha Analysis</span>'
        '<span style="font-size:0.78rem;color:#8b5cf6;margin-left:10px;">Your Ayurvedic constitution</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if dosha.get("error"):
        st.error(dosha.get("raw", "")[:300])
        return

    constitution = dosha.get("primary_constitution", "—")
    explanation  = dosha.get("explanation", "")

    with st.expander(f"Constitution: {constitution}", expanded=True):
        if explanation:
            st.markdown(
                _card(
                    f'<span style="color:#374151;font-size:0.9rem;line-height:1.7;">{explanation}</span>',
                    bg="#faf5ff", border_left="#7c3aed",
                ),
                unsafe_allow_html=True,
            )

        c1, c2 = st.columns(2)
        chars = dosha.get("characteristics", [])
        recs  = dosha.get("balance_recommendations", [])

        with c1:
            if chars:
                _section_label("Your Traits", "#7c3aed")
                items = "".join(
                    f'<div style="padding:5px 0;border-bottom:1px solid #ede9fe;'
                    f'font-size:0.85rem;color:#374151;">&#x2022; {c}</div>'
                    for c in chars
                )
                st.markdown(_card(items, bg="#faf5ff", border_color="#ede9fe"), unsafe_allow_html=True)

        with c2:
            if recs:
                _section_label("Balance Guidance", "#059669")
                items = "".join(
                    f'<div style="padding:5px 0;border-bottom:1px solid #d1fae5;'
                    f'font-size:0.85rem;color:#374151;">&#x2192; {r}</div>'
                    for r in recs
                )
                st.markdown(_card(items, bg="#f0fdf4", border_color="#d1fae5"), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Section 2 — Diet
# ---------------------------------------------------------------------------
def _render_diet(diet: Dict) -> None:
    st.markdown(
        '<div style="background:#f0f9ff;border-left:4px solid #0284c7;'
        'border-radius:0 10px 10px 0;padding:10px 16px;margin-bottom:4px;">'
        '<span style="font-size:1.05rem;font-weight:700;color:#0369a1;">Weekly Diet Plan</span>'
        '<span style="font-size:0.78rem;color:#0284c7;margin-left:10px;">Document-grounded recommendations</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if diet.get("error"):
        st.error(diet.get("raw", "")[:300])
        return

    # Include / Exclude color-coded
    rec_foods   = diet.get("recommended_foods", [])
    avoid_foods = diet.get("foods_to_avoid", [])

    if rec_foods or avoid_foods:
        c1, c2 = st.columns(2)
        with c1:
            if rec_foods:
                _section_label("Include", "#059669")
                chips = "".join(_pill(f, "#dcfce7", "#15803d") for f in rec_foods)
                st.markdown(
                    _card(chips, bg="#f0fdf4", border_left="#059669", border_color="#bbf7d0"),
                    unsafe_allow_html=True,
                )
        with c2:
            if avoid_foods:
                _section_label("Avoid or Limit", "#dc2626")
                chips = "".join(_pill(f, "#fee2e2", "#b91c1c") for f in avoid_foods)
                st.markdown(
                    _card(chips, bg="#fff5f5", border_left="#dc2626", border_color="#fecaca"),
                    unsafe_allow_html=True,
                )

    # Calendar view
    weekly = diet.get("weekly_chart", {})
    if not weekly:
        st.warning("No weekly chart available.")
    else:
        _section_label("7-Day Meal Plan", "#0284c7")
        day_tabs = st.tabs(DAY_SHORT)

        for tab, day in zip(day_tabs, DAYS):
            day_data = weekly.get(day, {})
            with tab:
                if not day_data:
                    st.caption("No data for this day.")
                    continue

                cols = st.columns(5)
                for col, (slot_key, label, default_time, color) in zip(cols, MEAL_SLOTS):
                    slot     = day_data.get(slot_key, {})
                    time_str = (slot.get("time", default_time) if isinstance(slot, dict) else default_time)
                    meal_raw = (slot.get("meal", "") if isinstance(slot, dict) else str(slot)) or "—"
                    items    = _split_meal(meal_raw)
                    icon     = MEAL_ICONS.get(slot_key, "")

                    bullet_rows = "".join(
                        f'<div style="font-size:0.78rem;color:#374151;padding:3px 0;'
                        f'border-bottom:1px solid {color}22;">&#x2022; {it}</div>'
                        for it in items
                    ) if items else '<div style="font-size:0.78rem;color:#94a3b8;">—</div>'

                    with col:
                        st.markdown(
                            f'<div style="border:1px solid {color}55;border-top:3px solid {color};'
                            f'border-radius:10px;padding:10px 10px 12px;background:#fff;min-height:160px;">'
                            f'<div style="font-size:1.1rem;margin-bottom:2px;">{icon}</div>'
                            f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;'
                            f'letter-spacing:.07em;color:{color};">{label}</div>'
                            f'<div style="font-size:0.65rem;color:#94a3b8;margin-bottom:8px;">{time_str}</div>'
                            f'{bullet_rows}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    # Summary
    summary = diet.get("summary", "")
    if summary:
        st.markdown(
            _card(
                f'<span style="font-size:0.72rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#0284c7;">Why this plan works for you</span>'
                f'<p style="margin:6px 0 0;font-size:0.88rem;color:#374151;line-height:1.65;">{summary}</p>',
                bg="#f0f9ff", border_left="#0284c7", border_color="#bae6fd",
            ),
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Section 3 — Products
# ---------------------------------------------------------------------------
def _render_product_card(item: Dict, idx: int) -> None:
    name     = item.get("product_name", "—")
    desc     = item.get("description", "")
    pairings = item.get("classical_pairings", [])
    conds    = item.get("conditions_addressed", [])
    generic  = not desc or "approved product document" in desc.lower()

    cond_pills    = "".join(_pill(c, "#e0f2fe", "#0369a1") for c in conds)
    pairing_pills = "".join(_pill(p, "#d1fae5", "#065f46") for p in pairings)

    st.markdown(
        f'<div style="border:1px solid #e2e8f0;border-radius:12px;padding:16px 18px;'
        f'margin-bottom:10px;background:#fff;'
        f'border-left:4px solid #0284c7;">'
        f'<div style="display:flex;align-items:flex-start;gap:12px;">'
        f'<div style="background:#eff6ff;border-radius:8px;padding:8px 12px;'
        f'font-size:1.1rem;font-weight:800;color:#0369a1;min-width:36px;text-align:center;">'
        f'{idx}</div>'
        f'<div style="flex:1;">'
        f'<div style="font-size:0.95rem;font-weight:700;color:#1e293b;margin-bottom:4px;">{name}</div>'
        + (f'<div style="font-size:0.82rem;color:#64748b;margin-bottom:8px;">{desc}</div>' if not generic and desc else "")
        + (f'<div style="margin-bottom:6px;">{cond_pills}</div>' if cond_pills else "")
        + (f'<div style="margin-top:4px;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#059669;">Classical Pairings</div>'
           f'<div>{pairing_pills}</div>' if pairing_pills else "")
        + f'</div></div></div>',
        unsafe_allow_html=True,
    )


def _render_products(products: Dict) -> None:
    st.markdown(
        '<div style="background:#f0fdf4;border-left:4px solid #059669;'
        'border-radius:0 10px 10px 0;padding:10px 16px;margin-bottom:4px;">'
        '<span style="font-size:1.05rem;font-weight:700;color:#065f46;">Products & Ayurvedic Solutions</span>'
        '<span style="font-size:0.78rem;color:#059669;margin-left:10px;">Extracted from approved documents</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if products.get("error"):
        st.error(products.get("raw", "")[:300])
        return

    strengthiva = products.get("strengthiva_products", [])
    extra_cf    = products.get("extra_classical_formulations", [])

    if not strengthiva and not extra_cf:
        st.warning("No matching products found in the approved product documents.")
        return

    if strengthiva:
        _section_label("Strengthiva & Proprietary Products", "#0284c7")
        visible  = strengthiva[:4]
        overflow = strengthiva[4:]
        for i, item in enumerate(visible, 1):
            _render_product_card(item, i)
        if overflow:
            with st.expander(f"+ {len(overflow)} more products"):
                for i, item in enumerate(overflow, len(visible) + 1):
                    _render_product_card(item, i)

    if extra_cf:
        with st.expander("Additional Classical Formulations"):
            rows = [extra_cf[i:i+3] for i in range(0, len(extra_cf), 3)]
            for row in rows:
                cols = st.columns(3)
                for col, item in zip(cols, row):
                    iname  = item.get("name", "—")
                    iconds = item.get("conditions_addressed", [])
                    with col:
                        st.markdown(
                            f'<div style="border:1px solid #d1fae5;border-radius:10px;'
                            f'padding:12px 14px;background:#f0fdf4;margin-bottom:8px;">'
                            f'<div style="font-size:0.88rem;font-weight:700;color:#065f46;">🌿 {iname}</div>'
                            + (f'<div style="font-size:0.75rem;color:#64748b;margin-top:4px;">For: {", ".join(iconds)}</div>' if iconds else "")
                            + "</div>",
                            unsafe_allow_html=True,
                        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_output_page(
    results: Dict[str, Any],
    profile: Dict[str, Any],
    on_refresh: Optional[Callable] = None,
) -> None:
    name = profile.get("name", "Friend")

    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.title(f"{name}'s Ayurvedic Health Report")
        diseases = [d for d in profile.get("existing_diseases", []) if d != "None"]
        goals    = profile.get("goals", [])
        tags     = diseases + goals
        if tags:
            st.caption("  ·  ".join(tags[:12]))
    with col_btn:
        st.write("")  # vertical align
        if on_refresh and st.button("Regenerate", help="Re-run with same profile"):
            on_refresh()

    st.divider()

    # Opening + metrics
    opening = results.get("opening_summary", "")
    if opening:
        _render_opening(opening, profile)

    st.divider()

    # Dosha
    _render_dosha(results.get("dosha", {}))

    st.divider()

    # Diet
    _render_diet(results.get("diet", {}))

    st.divider()

    # Products
    _render_products(results.get("product", {}))

    st.divider()

    # Download
    _make_download(results, profile, name)


def _make_download(results: Dict, profile: Dict, name: str) -> None:
    diseases = [d for d in profile.get("existing_diseases", []) if d != "None"]
    payload = {
        "report_metadata":  {"patient_name": name, "report_date": str(date.today()), "format_version": "3.1"},
        "patient_profile":  {k: profile.get(k) for k in (
            "age","gender","bmi","occupation","diet_type","sleep_hours","sleep_quality",
            "water_intake_liters","physical_activity","smoking","alcohol","daily_routine",
            "digestion","energy_level","fatigue","appetite","stress_level","anxiety",
            "mood","focus","body_pain","skin_issues","hair_issues","current_medications",
            "allergies","family_history","previous_ayurvedic_treatment","goals","other_goals",
        )} | {"existing_diseases": diseases},
        "opening_summary":         results.get("opening_summary", ""),
        "dosha_analysis":          results.get("dosha", {}),
        "diet_recommendations":    results.get("diet", {}),
        "product_recommendations": results.get("product", {}),
    }

    _, col, _ = st.columns([2, 2, 2])
    with col:
        st.download_button(
            label="Download Report (JSON)",
            data=json.dumps(payload, indent=2, ensure_ascii=False),
            file_name=f"ayurvedic_report_{name.lower().replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
