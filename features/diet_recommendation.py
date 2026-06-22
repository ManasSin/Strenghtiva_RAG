from typing import Dict


def build_diet_query(profile: Dict) -> str:
    conditions = []

    diseases = [d for d in profile.get("existing_diseases", []) if d != "None"]
    if diseases:
        conditions.extend(diseases)

    digestion = profile.get("digestion", "")
    if digestion not in ("Excellent", "Good"):
        conditions.append(digestion)

    if profile.get("energy_level") in ("Very Low", "Low"):
        conditions.append("low energy chronic fatigue weakness")

    if profile.get("stress_level") in ("High", "Very High"):
        conditions.append("high stress anxiety nervousness")

    bmi = profile.get("bmi", 22)
    if bmi > 27:
        conditions.append("weight management obesity overweight")
    elif bmi < 18.5:
        conditions.append("underweight low body weight nutrition")

    if profile.get("sleep_quality") in ("Poor", "Fair"):
        conditions.append("poor sleep insomnia")

    goals = profile.get("goals", [])
    goal_str = ", ".join(goals) if goals else "general wellness health"

    diet_type = profile.get("diet_type", "")
    age = profile.get("age", 30)
    gender = profile.get("gender", "")

    query = f"Ayurvedic diet food chart meal plan recommendations for {age} year old {gender} {diet_type} diet"
    if conditions:
        query += f" with conditions: {', '.join(conditions)}"
    query += f". Patient goals: {goal_str}. Recommended foods, foods to avoid, breakfast lunch dinner meal plan."
    return query
