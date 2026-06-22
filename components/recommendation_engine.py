"""
Four focused assistant prompts — each returns a validated dict.
All outputs are JSON-structured for downstream rendering and storage.
"""

import json
from typing import Any, Dict, List

from openai import OpenAI

_SAFETY_PREAMBLE = """CRITICAL SAFETY RULES (override everything else):
- Use ONLY the retrieved document chunks provided. Never use pretraining knowledge.
- Never invent product names, medicines, dosages, foods, or treatments.
- If a section has no document support, set its value to null or an empty list.
- Cite claims with chunk index numbers [1], [2] where helpful."""


def _context(chunks: List[Dict]) -> str:
    if not chunks:
        return "[NO CHUNKS RETRIEVED]"
    parts = []
    for i, c in enumerate(chunks, 1):
        src = c.get("source", "unknown")
        score = c.get("score", 0.0)
        parts.append(f"[{i}] source={src} relevance={score:.3f}\n{c['text'].strip()}")
    return "\n\n---\n\n".join(parts)


def _profile(p: Dict) -> str:
    diseases = [d for d in p.get("existing_diseases", []) if d != "None"]
    chronic  = [c for c in p.get("chronic_conditions", []) if c != "None"]
    pain     = [x for x in p.get("body_pain", []) if x != "No pain"]
    skin     = [x for x in p.get("skin_issues", []) if x != "None"]
    hair     = [x for x in p.get("hair_issues", []) if x != "None"]
    goals    = p.get("goals", [])
    return "\n".join([
        f"Name: {p.get('name','Patient')} | Age: {p.get('age','?')} | Gender: {p.get('gender','?')} | BMI: {p.get('bmi','?')}",
        f"Occupation: {p.get('occupation','?')} | Diet: {p.get('diet_type','?')}",
        f"Sleep: {p.get('sleep_hours','?')}h ({p.get('sleep_quality','?')}) | Water: {p.get('water_intake_liters','?')}L/day",
        f"Activity: {p.get('physical_activity','?')} | Routine: {p.get('daily_routine','?')}",
        f"Smoking: {p.get('smoking','?')} | Alcohol: {p.get('alcohol','?')}",
        f"Digestion: {p.get('digestion','?')} | Energy: {p.get('energy_level','?')} | Fatigue: {p.get('fatigue','?')}",
        f"Appetite: {p.get('appetite','?')} | Stress: {p.get('stress_level','?')} | Anxiety: {p.get('anxiety','?')}",
        f"Mood: {p.get('mood','?')} | Focus: {p.get('focus','?')}",
        f"Body Pain: {', '.join(pain) or 'None'} | Skin: {', '.join(skin) or 'None'} | Hair: {', '.join(hair) or 'None'}",
        f"Existing Diseases: {', '.join(diseases) or 'None'}",
        f"Chronic Conditions: {', '.join(chronic) or 'None'}",
        f"Current Medications: {p.get('current_medications','None') or 'None'}",
        f"Allergies: {p.get('allergies','None') or 'None'}",
        f"Goals: {', '.join(goals) or 'None'}",
        f"Other Goals: {p.get('other_goals','') or 'None'}",
    ])


class RecommendationEngine:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        # Stores the last prompts used — populated after each call
        self.last_prompts: Dict[str, Dict[str, str]] = {}

    def _call_json(self, system: str, user: str, label: str = "") -> Dict:
        if label:
            self.last_prompts[label] = {"system": system, "user": user}
        resp = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0,
        )
        raw = resp.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "LLM returned non-JSON", "raw": raw}

    # -----------------------------------------------------------------------
    # PROMPT 0 — Opening Summary (strengths-forward, parameter-aware)
    # -----------------------------------------------------------------------
    def generate_opening_summary(self, profile: Dict, dosha: Dict) -> str:
        goals        = profile.get("goals", [])
        constitution = dosha.get("primary_constitution", "")
        name         = profile.get("name", "Friend")

        # ---- Identify genuine strengths (show directly) ----
        strengths = []
        sleep_h = profile.get("sleep_hours", 0)
        sleep_q = profile.get("sleep_quality", "")
        if sleep_h >= 7 and sleep_q in ("Excellent", "Good"):
            strengths.append(f"a restorative {sleep_h}-hour sleep rhythm")
        water = profile.get("water_intake_liters", 0)
        if water >= 2.5:
            strengths.append(f"excellent hydration of {water}L daily")
        activity = profile.get("physical_activity", "")
        if any(w in activity for w in ("Moderate", "Active", "Very Active")):
            strengths.append("an active lifestyle that keeps your vitality alive")
        diet = profile.get("diet_type", "")
        if any(w in diet for w in ("Vegetarian", "Vegan")):
            strengths.append(f"a mindful {diet.lower()} diet — a natural Ayurvedic ally")
        med = profile.get("meditation_yoga", "")
        if med in ("Daily", "Weekly"):
            strengths.append(f"a {med.lower()} mindfulness practice")
        if profile.get("focus") in ("Excellent", "Good"):
            strengths.append("sharp mental clarity")

        # ---- Identify moderate areas (reframe as growing strengths) ----
        growing = []
        if sleep_h >= 5 and sleep_q in ("Fair", "Poor") and not any("sleep" in s for s in strengths):
            growing.append("deepening the quality of your rest")
        if 1.5 <= water < 2.5 and not any("hydration" in s for s in strengths):
            growing.append("building an even stronger hydration habit")
        if profile.get("energy_level") in ("Moderate",):
            growing.append("unlocking fuller energy reserves")
        if med in ("Occasional", "None") and not any("mindfulness" in s for s in strengths):
            growing.append("a blossoming inner calm")
        if profile.get("digestion") in ("Good",):
            growing.append("fine-tuning your already decent digestion")

        # ---- Goals to mention (top 2, positively framed) ----
        top_goals = goals[:2]

        strength_str = (", ".join(strengths[:3]) + " — ") if strengths else ""
        growing_str  = (" and ".join(growing[:2]) + " are opportunities this plan targets") if growing else ""
        goals_str    = " and ".join(top_goals) if top_goals else "overall wellness"

        system = """You are a clinical Ayurvedic report writer. Write a brief, factual opening note.

STRICT RULES:
1. Use the person's name once at the start.
2. State 1-2 specific strengths from the data given — factual, not flowery.
3. Mention 1 area to improve, framed as a next step.
4. State their primary goal plainly.
5. NEVER mention diseases, illness, or medical conditions.
6. NEVER use words like: journey, remarkable, seeds, transformation, empower, excited, meaningful, nurture, blossoming, truly, shining, vibrant.
7. Exactly 2 sentences. Simple English. No adjective overload. No poetry.
8. HARD LIMIT: 50 words total. Count before returning."""

        user = f"""Write a 2-sentence (max 50 words) opening note for {name}'s Ayurvedic report.

Name: {name} | Constitution: {constitution or 'balanced'} | Age: {profile.get('age','?')}
Key strengths (mention specifically): {strength_str or 'consistent health practices'}
Area to improve (state plainly): {growing_str or 'hydration and routine'}
Goal: {goals_str}"""

        self.last_prompts["summary"] = {"system": system, "user": user}
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    # -----------------------------------------------------------------------
    # PROMPT 1 — Dosha Analysis
    # -----------------------------------------------------------------------
    def analyze_dosha(self, profile: Dict, chunks: List[Dict]) -> Dict:
        SYSTEM = f"""{_SAFETY_PREAMBLE}

You are an Ayurvedic Dosha Analysis assistant.

TASK: Determine the patient's dominant dosha combination.

VALID COMBINATIONS (pick exactly one):
  "Vata + Pitta"   |   "Pitta + Kapha"   |   "Vata + Kapha"

Vata indicators: thin/low BMI, dry skin, constipation, anxiety, poor sleep,
  variable appetite, joint pain, hair fall, irregular routine.
Pitta indicators: medium build, acidity/GERD, high stress, acne, oily skin,
  sharp hunger, inflammation, intensity.
Kapha indicators: heavy/high BMI, slow digestion, low energy, excess sleep,
  obesity, oily skin, lethargy, respiratory issues.

OUTPUT — valid JSON only:
{{
  "primary_constitution": "<one of the 3 pairs>",
  "explanation": "<2-3 sentences grounded in retrieved chunks or profile traits>",
  "characteristics": ["<trait 1>", "<trait 2>", "<trait 3>", "<trait 4>"],
  "balance_recommendations": ["<rec 1>", "<rec 2>", "<rec 3>", "<rec 4>"]
}}"""

        USER = f"""=== PATIENT PROFILE ===
{_profile(profile)}

=== RETRIEVED DOSHA DOCUMENTS ===
{_context(chunks)}

Return the JSON dosha analysis."""

        result = self._call_json(SYSTEM, USER, label="dosha")
        valid = {"Vata + Pitta", "Pitta + Kapha", "Vata + Kapha"}
        if result.get("primary_constitution") not in valid:
            result["primary_constitution"] = "Vata + Pitta"
        return result

    # -----------------------------------------------------------------------
    # PROMPT 2 — Weekly Diet Chart (with diet-type guardrails)
    # -----------------------------------------------------------------------
    def get_diet_recommendations(self, profile: Dict, chunks: List[Dict]) -> Dict:
        diet_type   = profile.get("diet_type", "Mixed")
        diseases    = [d for d in profile.get("existing_diseases", []) if d != "None"]
        goals       = profile.get("goals", [])

        # Build strict dietary restriction line
        restriction_lines = []
        diet_lower = diet_type.lower()
        if "vegan" in diet_lower:
            restriction_lines.append("VEGAN: exclude ALL animal products — no meat, poultry, seafood, eggs, dairy, honey.")
        elif "vegetarian" in diet_lower and "egg" not in diet_lower:
            restriction_lines.append("VEGETARIAN: exclude all meat, poultry, seafood, and eggs. Dairy is allowed.")
        elif "eggetarian" in diet_lower:
            restriction_lines.append("EGGETARIAN: eggs are allowed. Exclude all meat, poultry, and seafood.")
        elif "non-vegetarian" in diet_lower:
            restriction_lines.append("NON-VEGETARIAN: all foods are allowed in moderation.")
        else:
            restriction_lines.append("MIXED diet: use balanced options, prefer plant-based where possible.")

        restriction_block = "\n".join(restriction_lines)

        SYSTEM = f"""{_SAFETY_PREAMBLE}

You are an Ayurvedic Diet Recommendation assistant.

STRICT DIETARY RESTRICTIONS — violating these is a critical error:
{restriction_block}
Never include any ingredient that violates the patient's diet type above.

TASK: Generate a complete 7-day Ayurvedic diet chart.

RULES:
1. Use ONLY foods mentioned or consistent with the retrieved diet documents.
2. All 7 days: Monday through Sunday. Each day: 5 meal slots.
3. Vary meals meaningfully across days.
4. Each slot: "time" and "meal" (specific, appetising description — not generic).
5. Base recommendations on the patient's diseases, goals, and digestion.

OUTPUT — valid JSON only:
{{
  "weekly_chart": {{
    "Monday":    {{"breakfast": {{"time": "7:30 AM", "meal": "..."}}, "mid_morning": {{"time": "10:30 AM", "meal": "..."}}, "lunch": {{"time": "1:00 PM", "meal": "..."}}, "evening": {{"time": "4:30 PM", "meal": "..."}}, "dinner": {{"time": "7:30 PM", "meal": "..."}}}},
    "Tuesday":   {{}},
    "Wednesday": {{}},
    "Thursday":  {{}},
    "Friday":    {{}},
    "Saturday":  {{}},
    "Sunday":    {{}}
  }},
  "recommended_foods": ["<food 1>", ...],
  "foods_to_avoid":    ["<food 1>", ...],
  "summary": "<2-3 sentences on why this plan suits the patient>"
}}"""

        USER = f"""=== PATIENT PROFILE ===
{_profile(profile)}

DISEASES: {', '.join(diseases) or 'None'}
GOALS:    {', '.join(goals) or 'General wellness'}
DIET:     {diet_type}

=== RETRIEVED DIET DOCUMENTS ===
{_context(chunks)}

Generate the 7-day weekly diet chart JSON, strictly respecting the dietary restrictions."""

        return self._call_json(SYSTEM, USER, label="diet")

    # -----------------------------------------------------------------------
    # PROMPT 3 — Product & Solution Recommendations (product-centric)
    # -----------------------------------------------------------------------
    def get_product_recommendations(self, profile: Dict, chunks: List[Dict]) -> Dict:
        diseases = [d for d in profile.get("existing_diseases", []) if d != "None"]
        chronic  = [c for c in profile.get("chronic_conditions", []) if c != "None"]
        extras = []
        if profile.get("digestion") not in ("Excellent", "Good"):
            extras.append(profile.get("digestion", ""))
        extras.extend([s for s in profile.get("skin_issues", []) if s != "None"])
        extras.extend([h for h in profile.get("hair_issues", []) if h != "None"])
        if profile.get("stress_level") in ("High", "Very High"):
            extras.append("Stress / Anxiety")
        all_conditions = diseases + chronic + extras

        SYSTEM = f"""{_SAFETY_PREAMBLE}

You are an Ayurvedic Product & Solution Recommendation assistant.

DOCUMENT FORMAT: "Disease- Product1, Product2... Classical medications- Formula1, Formula2"

Strengthiva proprietary products = tablet / syrup / tea / drops / oil / powder / mix items.
Classical formulations = names ending in Vati, Kashaya, Gritha, Churna, Rasa, Louha,
  Arista/Arishta, Guggulu, Rasayana, Kalpa, Taila etc.

TASK: For each patient condition, extract products from the document.
Then GROUP BY PRODUCT — not by disease.

For each Strengthiva product:
- Write a SHORT description (1 sentence) from document context.
- List which of the patient's conditions it addresses.
- List the classical formulations recommended for those SAME conditions (classical_pairings).

Any classical formulations not naturally paired with a Strengthiva product go into
extra_classical_formulations.

EXACT names only — never rephrase or invent.

OUTPUT — valid JSON only:
{{
  "strengthiva_products": [
    {{
      "product_name": "<exact name>",
      "description": "<one sentence from document>",
      "classical_pairings": ["<formula 1>", "<formula 2>"],
      "conditions_addressed": ["<cond 1>", "<cond 2>"]
    }}
  ],
  "extra_classical_formulations": [
    {{
      "name": "<exact name>",
      "conditions_addressed": ["<cond 1>"]
    }}
  ]
}}"""

        USER = f"""=== PATIENT CONDITIONS TO LOOK UP ===
{chr(10).join(f'- {c}' for c in all_conditions) if all_conditions else '- General health / wellness'}

=== RETRIEVED PRODUCT DOCUMENTS ===
{_context(chunks)}

Extract all relevant products and formulations, grouped by product."""

        return self._call_json(SYSTEM, USER, label="product")
