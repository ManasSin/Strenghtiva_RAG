from typing import Dict


def build_product_query(profile: Dict) -> str:
    targets = []

    diseases = [d for d in profile.get("existing_diseases", []) if d != "None"]
    targets.extend(diseases)

    goals = profile.get("goals", [])
    targets.extend(goals)

    if profile.get("energy_level") in ("Very Low", "Low"):
        targets.append("energy booster stamina fatigue relief supplement")

    if profile.get("stress_level") in ("High", "Very High"):
        targets.append("stress relief adaptogen anxiety management")

    digestion = profile.get("digestion", "")
    if digestion not in ("Excellent", "Good"):
        targets.append("digestive health gut support probiotic")

    skin_issues = [s for s in profile.get("skin_issues", []) if s != "None"]
    if skin_issues:
        targets.append(f"skin care {' '.join(skin_issues)} ayurvedic")

    hair_issues = [h for h in profile.get("hair_issues", []) if h != "None"]
    if hair_issues:
        targets.append(f"hair care {' '.join(hair_issues)} supplement")

    bmi = profile.get("bmi", 22)
    if bmi > 27:
        targets.append("weight management metabolism fat burn")
    elif bmi < 18.5:
        targets.append("weight gain nutrition supplement")

    if profile.get("sleep_quality") in ("Poor", "Fair"):
        targets.append("sleep improvement insomnia natural remedy")

    if profile.get("immunity") or "Improve immunity" in goals:
        targets.append("immunity booster immune system support")

    query = "Ayurvedic herbal product supplement recommendation"
    if targets:
        query += f" for: {', '.join(targets[:6])}"

    return query
