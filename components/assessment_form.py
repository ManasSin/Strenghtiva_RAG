"""
Multi-tab health assessment form.
Returns a structured profile dict on submission, None otherwise.
Add new tabs/questions here without touching the recommendation engine.
"""

from typing import Any, Dict, Optional

import streamlit as st


def render_assessment_form() -> Optional[Dict[str, Any]]:
    st.markdown("### Complete all tabs, then click **Generate My Health Report**.")

    (
        tab_basic,
        tab_lifestyle,
        tab_physical,
        tab_mental,
        tab_medical,
        tab_goals,
    ) = st.tabs([
        "👤 Basic Information",
        "🏃 Lifestyle",
        "💪 Physical Health",
        "🧠 Mental Health",
        "🏥 Medical History",
        "🎯 Goals",
    ])

    profile: Dict[str, Any] = {}

    # ------------------------------------------------------------------ Tab 1
    with tab_basic:
        st.subheader("Basic Information")
        c1, c2 = st.columns(2)
        with c1:
            profile["name"] = st.text_input("Full Name *", placeholder="Enter your name")
            profile["age"] = st.number_input("Age *", min_value=1, max_value=120, value=30)
            profile["gender"] = st.selectbox("Gender *", ["Male", "Female", "Other", "Prefer not to say"])
        with c2:
            profile["height_cm"] = st.number_input("Height (cm) *", min_value=50, max_value=250, value=170)
            profile["weight_kg"] = st.number_input("Weight (kg) *", min_value=10.0, max_value=300.0, value=70.0, step=0.5)
            profile["occupation"] = st.text_input("Occupation", placeholder="e.g. Software Engineer, Teacher")

        if profile["height_cm"] > 0:
            bmi = profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2)
            profile["bmi"] = round(bmi, 1)
            cat = (
                "Underweight" if bmi < 18.5
                else "Normal weight" if bmi < 25
                else "Overweight" if bmi < 30
                else "Obese"
            )
            st.info(f"Calculated BMI: **{profile['bmi']}** — {cat}")

    # ------------------------------------------------------------------ Tab 2
    with tab_lifestyle:
        st.subheader("Lifestyle")
        c1, c2 = st.columns(2)
        with c1:
            profile["sleep_hours"] = st.slider("Sleep (hours/night)", 3, 12, 7)
            profile["sleep_quality"] = st.selectbox(
                "Sleep Quality", ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
            )
            profile["water_intake_liters"] = st.slider(
                "Water Intake (liters/day)", 0.5, 5.0, 2.0, step=0.5
            )
            profile["physical_activity"] = st.selectbox(
                "Physical Activity Level",
                [
                    "Sedentary (no exercise)",
                    "Light (1-2 days/week)",
                    "Moderate (3-5 days/week)",
                    "Active (6-7 days/week)",
                    "Very Active (athlete / physical labor)",
                ],
            )
        with c2:
            profile["smoking"] = st.selectbox(
                "Smoking", ["Never", "Former Smoker", "Occasional (socially)", "Daily"]
            )
            profile["alcohol"] = st.selectbox(
                "Alcohol Consumption", ["Never", "Rarely (few times/year)", "Weekly", "Daily"]
            )
            profile["diet_type"] = st.selectbox(
                "Diet Type",
                ["Vegetarian", "Vegan", "Non-Vegetarian", "Eggetarian", "Mixed / Flexitarian"],
            )
            profile["daily_routine"] = st.selectbox(
                "Daily Routine",
                [
                    "Regular (fixed wake/sleep timings)",
                    "Irregular (shift work / travel)",
                    "Sedentary (desk job, minimal movement)",
                    "Physically demanding (manual labor)",
                ],
            )

    # ------------------------------------------------------------------ Tab 3
    with tab_physical:
        st.subheader("Physical Health")
        c1, c2 = st.columns(2)
        with c1:
            profile["digestion"] = st.selectbox(
                "Digestion",
                [
                    "Excellent",
                    "Good",
                    "Bloating / Gas",
                    "Constipation",
                    "Acidity / GERD",
                    "Loose stools / Diarrhea",
                    "IBS symptoms",
                ],
            )
            profile["energy_level"] = st.select_slider(
                "Energy Level", ["Very Low", "Low", "Moderate", "High", "Very High"]
            )
            profile["fatigue"] = st.selectbox(
                "Fatigue", ["Never", "Occasionally", "Frequently", "Chronic fatigue"]
            )
            profile["appetite"] = st.selectbox(
                "Appetite", ["Normal", "Low appetite", "High / Excessive appetite", "Variable / Irregular"]
            )
        with c2:
            profile["body_pain"] = st.multiselect(
                "Body Pain / Discomfort",
                [
                    "No pain",
                    "Back pain",
                    "Joint pain",
                    "Neck / Shoulder pain",
                    "Headache / Migraine",
                    "Muscle cramps",
                    "Knee pain",
                    "Chest tightness",
                ],
            )
            profile["skin_issues"] = st.multiselect(
                "Skin Issues",
                ["None", "Acne", "Dry skin", "Oily skin", "Eczema", "Psoriasis", "Rashes", "Pigmentation / Dark spots"],
            )
            profile["hair_issues"] = st.multiselect(
                "Hair Issues",
                ["None", "Hair fall / Thinning", "Dandruff", "Premature greying", "Dry / Brittle hair", "Oily scalp"],
            )

    # ------------------------------------------------------------------ Tab 4
    with tab_mental:
        st.subheader("Mental Health")
        c1, c2 = st.columns(2)
        with c1:
            profile["stress_level"] = st.select_slider(
                "Stress Level", ["Very Low", "Low", "Moderate", "High", "Very High"]
            )
            profile["anxiety"] = st.selectbox(
                "Anxiety / Worry", ["None", "Mild", "Moderate", "Severe"]
            )
            profile["mood"] = st.selectbox(
                "General Mood",
                ["Very Positive", "Positive", "Neutral / Stable", "Low / Sad", "Very Low / Depressed"],
            )
        with c2:
            profile["focus"] = st.selectbox(
                "Concentration / Focus",
                ["Excellent", "Good", "Average", "Poor", "Very Poor / Brain fog"],
            )
            profile["emotional_wellbeing"] = st.selectbox(
                "Emotional Wellbeing",
                [
                    "Stable",
                    "Mostly stable",
                    "Occasional mood swings",
                    "Frequent mood swings",
                    "Emotional instability",
                ],
            )
            profile["meditation_yoga"] = st.selectbox(
                "Meditation / Yoga Practice", ["None", "Occasional", "Weekly", "Daily"]
            )

    # ------------------------------------------------------------------ Tab 5
    with tab_medical:
        st.subheader("Medical History")
        c1, c2 = st.columns(2)
        with c1:
            profile["existing_diseases"] = st.multiselect(
                "Existing Diseases / Conditions",
                [
                    "None",
                    "Diabetes (Type 1)",
                    "Diabetes (Type 2)",
                    "Pre-diabetes",
                    "Hypertension (High BP)",
                    "Hypothyroidism",
                    "Hyperthyroidism",
                    "PCOD / PCOS",
                    "Asthma / Respiratory",
                    "Arthritis / Joint disorder",
                    "Heart disease",
                    "Kidney disease",
                    "Liver disease",
                    "Anemia",
                    "Obesity",
                    "Depression / Anxiety disorder",
                    "Other",
                ],
            )
            profile["chronic_conditions"] = st.multiselect(
                "Chronic Conditions",
                [
                    "None",
                    "Chronic fatigue syndrome",
                    "Chronic pain",
                    "Autoimmune disorder",
                    "Hormonal imbalance",
                    "Migraine (chronic)",
                    "Other",
                ],
            )
        with c2:
            profile["current_medications"] = st.text_area(
                "Current Medications (if any)",
                placeholder="List medications you are currently taking...",
                height=90,
            )
            profile["allergies"] = st.text_input(
                "Known Allergies",
                placeholder="e.g. penicillin, peanuts, latex",
            )
            profile["family_history"] = st.multiselect(
                "Family Medical History",
                ["None", "Diabetes", "Heart disease", "Cancer", "Hypertension", "Thyroid", "Mental health conditions", "Other"],
            )

        profile["previous_ayurvedic_treatment"] = st.selectbox(
            "Previous Ayurvedic Treatment",
            [
                "Never tried",
                "Yes — with positive results",
                "Yes — with mixed results",
                "Yes — without noticeable results",
            ],
        )

    # ------------------------------------------------------------------ Tab 6
    with tab_goals:
        st.subheader("Health Goals")
        st.markdown("Select **all** goals you want to work towards:")

        c1, c2, c3 = st.columns(3)
        with c1:
            g_weight    = st.checkbox("⚖️  Weight management")
            g_sleep     = st.checkbox("😴  Better sleep")
            g_digestion = st.checkbox("🍽️  Improve digestion")
            g_energy    = st.checkbox("⚡  Improve energy levels")
        with c2:
            g_stress    = st.checkbox("🧘  Reduce stress & anxiety")
            g_immunity  = st.checkbox("🛡️  Improve immunity")
            g_skin      = st.checkbox("✨  Better skin & hair")
            g_hormones  = st.checkbox("⚙️  Hormonal balance")
        with c3:
            g_pain      = st.checkbox("🦴  Reduce body pain")
            g_focus     = st.checkbox("🎯  Better focus & memory")
            g_detox     = st.checkbox("🌿  Detox / cleanse")
            g_longevity = st.checkbox("💚  Overall longevity & wellness")

        profile["goals"] = [
            label
            for label, checked in [
                ("Weight management", g_weight),
                ("Better sleep", g_sleep),
                ("Improve digestion", g_digestion),
                ("Improve energy levels", g_energy),
                ("Reduce stress and anxiety", g_stress),
                ("Improve immunity", g_immunity),
                ("Better skin and hair", g_skin),
                ("Hormonal balance", g_hormones),
                ("Reduce body pain", g_pain),
                ("Better focus and memory", g_focus),
                ("Detox and cleanse", g_detox),
                ("Overall longevity and wellness", g_longevity),
            ]
            if checked
        ]

        profile["other_goals"] = st.text_area(
            "Other specific goals or concerns",
            placeholder="Describe any additional health goals, symptoms, or concerns...",
            height=80,
        )

    # ------------------------------------------------------------------ Submit
    st.divider()
    _, c_mid, _ = st.columns([1, 2, 1])
    with c_mid:
        submitted = st.button(
            "🌿 Generate My Ayurvedic Health Report",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        errors = []
        if not profile.get("name", "").strip():
            errors.append("Name is required (Basic Information tab).")
        if not profile.get("goals"):
            errors.append("Select at least one health goal (Goals tab).")
        if errors:
            for e in errors:
                st.error(e)
            return None
        return profile

    return None
