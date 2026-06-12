from __future__ import annotations

from typing import Any

import pandas as pd


RISK_ORDER = {
    "low": 0,
    "low risk": 0,
    "medium": 1,
    "medium risk": 1,
    "high": 2,
    "high risk": 2,
}

RISK_LABELS = {
    0: "Low Risk",
    1: "Medium Risk",
    2: "High Risk",
}

RISK_SCORE_BY_LEVEL = {
    0: 18,
    1: 52,
    2: 82,
}


def normalize_risk_label(value: Any) -> str:
    """Convert model labels such as High/Medium/Low into dashboard labels."""
    key = str(value).strip().lower().replace("_", " ")
    return RISK_LABELS.get(RISK_ORDER.get(key, 1), str(value))


def risk_level_index(value: Any) -> int:
    key = str(value).strip().lower().replace("_", " ")
    return RISK_ORDER.get(key, 1)


def get_probability_payload(model: Any, input_df: pd.DataFrame, prediction: Any) -> dict[str, Any]:
    """Return model probabilities, confidence, and a 0-100 risk score."""
    if not hasattr(model, "predict_proba"):
        level = risk_level_index(prediction)
        return {
            "confidence": None,
            "probability": None,
            "risk_score": RISK_SCORE_BY_LEVEL[level],
            "class_probabilities": {},
        }

    probabilities = model.predict_proba(input_df)[0]
    classes = getattr(model, "classes_", [])
    class_probabilities: dict[str, float] = {}

    for label, probability in zip(classes, probabilities):
        class_probabilities[normalize_risk_label(label)] = round(float(probability), 4)

    predicted_label = normalize_risk_label(prediction)
    confidence = class_probabilities.get(predicted_label)
    if confidence is None and len(probabilities):
        confidence = float(max(probabilities))

    risk_score = _weighted_risk_score(class_probabilities, prediction)

    return {
        "confidence": round(float(confidence), 4) if confidence is not None else None,
        "probability": round(float(confidence), 4) if confidence is not None else None,
        "risk_score": risk_score,
        "class_probabilities": class_probabilities,
    }


def _weighted_risk_score(class_probabilities: dict[str, float], prediction: Any) -> int:
    if not class_probabilities:
        return RISK_SCORE_BY_LEVEL[risk_level_index(prediction)]

    weighted = 0.0
    anchors = {
        "Low Risk": 18,
        "Medium Risk": 52,
        "High Risk": 86,
    }
    for label, probability in class_probabilities.items():
        weighted += anchors.get(label, 52) * probability

    return int(round(max(0, min(100, weighted))))


def generate_explanations(data: Any) -> list[str]:
    explanations: list[str] = []

    if data.bmi >= 30:
        explanations.append("BMI is significantly above the healthy range and increases the risk profile.")
    elif data.bmi >= 25:
        explanations.append("BMI is above the healthy range and moderately increases risk.")
    else:
        explanations.append("BMI is within a healthier range and helps reduce risk.")

    if data.smoker:
        explanations.append("Smoking status contributes heavily to the predicted risk segment.")
    else:
        explanations.append("Non-smoking status reduces the overall lifestyle risk.")

    if data.age >= 60:
        explanations.append("Senior age group increases expected health and underwriting risk.")
    elif data.age >= 45:
        explanations.append("Middle-aged profile adds moderate age-related risk.")
    else:
        explanations.append("Age group does not add a major risk penalty.")

    if data.income_lpa < 5:
        explanations.append("Lower income can affect affordability and increases the risk profile.")
    elif data.income_lpa >= 20:
        explanations.append("Higher income improves affordability and may reduce business risk.")

    if data.city_tier == 3:
        explanations.append("Tier 3 city profile may introduce higher uncertainty in the risk model.")

    return explanations


def business_rule_contributions(data: Any) -> list[dict[str, Any]]:
    contributions = [
        _contribution("BMI", _score_bmi(data.bmi), data.bmi),
        _contribution("Smoking", 25 if data.smoker else -12, "Smoker" if data.smoker else "Non-smoker"),
        _contribution("Age Group", _score_age(data.age), data.age_group),
        _contribution("Income", _score_income(data.income_lpa), data.income_lpa),
        _contribution("City Tier", _score_city_tier(data.city_tier), data.city_tier),
        _contribution("Occupation", _score_occupation(data.occupation), data.occupation),
    ]
    return sorted(contributions, key=lambda item: abs(item["impact"]), reverse=True)


def shap_contributions(model: Any, input_df: pd.DataFrame, prediction: Any) -> list[dict[str, Any]] | None:
    """Best-effort SHAP integration for a sklearn Pipeline.

    The app uses business-rule contributions if SHAP is unavailable or if the
    pipeline cannot be transformed cleanly in the runtime environment.
    """
    try:
        import numpy as np
        import shap

        preprocessor = model.named_steps["preprocessor"]
        classifier = model.named_steps["classifier"]
        transformed = preprocessor.transform(input_df)
        feature_names = preprocessor.get_feature_names_out()

        explainer = shap.TreeExplainer(classifier)
        shap_values = explainer.shap_values(transformed)
        class_labels = list(getattr(classifier, "classes_", getattr(model, "classes_", [])))
        predicted_index = _predicted_class_index(class_labels, prediction)

        if isinstance(shap_values, list):
            row_values = shap_values[predicted_index][0]
        else:
            values = np.asarray(shap_values)
            if values.ndim == 3:
                row_values = values[0, :, predicted_index]
            else:
                row_values = values[0]

        grouped: dict[str, float] = {}
        for name, value in zip(feature_names, row_values):
            original_name = _original_feature_name(str(name))
            grouped[original_name] = grouped.get(original_name, 0.0) + float(value)

        max_abs = max((abs(value) for value in grouped.values()), default=0.0)
        if max_abs == 0:
            return None

        results = []
        for feature, value in grouped.items():
            impact = int(round((value / max_abs) * 40))
            results.append(_contribution(feature, impact, "SHAP"))

        return sorted(results, key=lambda item: abs(item["impact"]), reverse=True)
    except Exception:
        return None


def generate_recommendations(data: Any) -> list[str]:
    recommendations: list[str] = []

    if data.bmi > 30:
        recommendations.append("Reduce BMI below 25 through a structured nutrition and activity plan.")
    elif data.bmi > 25:
        recommendations.append("Aim to bring BMI into the 18.5-24.9 range.")

    if data.smoker:
        recommendations.append("Smoking cessation is strongly recommended to reduce lifestyle risk.")

    if data.age > 50:
        recommendations.append("Schedule regular preventive health screenings.")

    if data.income_lpa < 5:
        recommendations.append("Review premium affordability and consider flexible coverage options.")

    if not recommendations:
        recommendations.append("Maintain current healthy indicators and review insurance needs annually.")

    return recommendations


def rank_risk_drivers(contributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(contributions, key=lambda item: abs(item["impact"]), reverse=True)
    return [
        {
            "rank": index + 1,
            "feature": item["feature"],
            "impact": item["impact"],
            "direction": item["direction"],
        }
        for index, item in enumerate(ranked)
    ]


def _contribution(feature: str, impact: int, value: Any) -> dict[str, Any]:
    return {
        "feature": feature,
        "impact": int(impact),
        "direction": "Increased Risk" if impact > 0 else "Reduced Risk" if impact < 0 else "Neutral",
        "value": value,
    }


def _score_bmi(bmi: float) -> int:
    if bmi >= 35:
        return 40
    if bmi >= 30:
        return 32
    if bmi >= 27:
        return 20
    if bmi >= 25:
        return 10
    if bmi < 18.5:
        return 8
    return -12


def _score_age(age: int) -> int:
    if age >= 60:
        return 28
    if age >= 45:
        return 18
    if age >= 25:
        return 6
    return -5


def _score_income(income_lpa: float) -> int:
    if income_lpa < 5:
        return 18
    if income_lpa < 10:
        return 8
    if income_lpa >= 25:
        return -15
    if income_lpa >= 15:
        return -8
    return 0


def _score_city_tier(city_tier: int) -> int:
    if city_tier == 1:
        return -5
    if city_tier == 2:
        return 4
    return 10


def _score_occupation(occupation: str) -> int:
    scores = {
        "student": -8,
        "government_job": -5,
        "private_job": 0,
        "freelancer": 8,
        "business_owner": 10,
        "unemployed": 16,
        "retired": 18,
    }
    return scores.get(occupation, 0)


def _original_feature_name(name: str) -> str:
    clean = name.replace("cat__", "").replace("num__", "")
    for feature in ["age_group", "lifestyle_risk", "occupation", "city_tier", "bmi", "income_lpa"]:
        if clean == feature or clean.startswith(f"{feature}_"):
            return feature
    return clean


def _predicted_class_index(class_labels: list[Any], prediction: Any) -> int:
    predicted_label = normalize_risk_label(prediction)
    for index, label in enumerate(class_labels):
        if normalize_risk_label(label) == predicted_label:
            return index
    return min(risk_level_index(prediction), max(len(class_labels) - 1, 0))
