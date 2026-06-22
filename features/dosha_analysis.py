from typing import Dict


def build_dosha_query(profile: Dict) -> str:
    traits = []

    bmi = profile.get("bmi", 22)
    if bmi < 18.5:
        traits.append("underweight thin body frame light")
    elif bmi > 27:
        traits.append("heavy body weight overweight kapha")

    digestion = profile.get("digestion", "")
    if digestion in ("Bloating/Gas", "IBS symptoms"):
        traits.append("bloating gas irregular digestion vata")
    elif digestion == "Acidity/GERD":
        traits.append("acidity heartburn pitta digestion")
    elif digestion == "Constipation":
        traits.append("constipation dry vata digestion")

    energy = profile.get("energy_level", "")
    if energy in ("Very Low", "Low"):
        traits.append("low energy lethargy heaviness kapha")

    stress = profile.get("stress_level", "")
    if stress in ("High", "Very High"):
        traits.append("anxiety worry overthinking vata mental")

    sleep_quality = profile.get("sleep_quality", "")
    if sleep_quality in ("Poor", "Fair"):
        traits.append("poor sleep insomnia restlessness vata")

    skin = profile.get("skin_issues", [])
    if "Acne" in skin or "Oily skin" in skin:
        traits.append("acne oily skin inflammation pitta")
    if "Dry skin" in skin:
        traits.append("dry rough skin vata")

    pain = profile.get("body_pain", [])
    if "Joint pain" in pain or "Back pain" in pain:
        traits.append("joint pain stiffness vata arthritis")

    appetite = profile.get("appetite", "")
    if appetite == "High appetite":
        traits.append("strong hunger sharp appetite pitta")
    elif appetite == "Low appetite":
        traits.append("low appetite poor digestion kapha")

    age = profile.get("age", 30)
    gender = profile.get("gender", "")

    query = f"Ayurvedic dosha analysis constitution for {age} year old {gender}"
    if traits:
        query += " with " + ", ".join(traits)
    query += (
        ". Determine Vata Pitta Kapha dominant dosha combination. "
        "Vata Pitta Kapha constitution characteristics balance recommendations."
    )
    return query
