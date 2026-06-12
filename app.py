# cd "c:\Users\aryan\PW DS\fastapi\fastapi-demo-api-main"
# .\.venv\Scripts\python.exe -m uvicorn app:app --reload



# 2nd terminal:
# cd "c:\Users\aryan\PW DS\fastapi\fastapi-demo-api-main"
# .\.venv\Scripts\python.exe -m streamlit run frontend.py


from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query
from schema.user_input import UserInput
import pickle
import pandas as pd

from services.history_store import PredictionHistoryStore
from services.risk_engine import (
    business_rule_contributions,
    generate_explanations,
    generate_recommendations,
    get_probability_payload,
    normalize_risk_label,
    rank_risk_drivers,
    shap_contributions,
)

# uvicorn app:app --reload
# change terminal to run frontend
# cd fastapi-demo-api-main
# streamlit run frontend.py

# ML flow metadata
MODEL_VERSION = '1.8.0'
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
DATABASE_PATH = BASE_DIR / "data" / "insurance_predictions.db"

# Load the ml model
with MODEL_PATH.open('rb') as f:
    model = pickle.load(f)

app = FastAPI()
history_store = PredictionHistoryStore(DATABASE_PATH)

@app.get('/')
def home():
    return {'msg': 'Insurance prediction API'}

@app.get('/health')
def health_check():
    return {
        'status': "ok",
        "version": MODEL_VERSION,
        'model_loaded': model is not None,
        'database_path': str(DATABASE_PATH)
    }

@app.post('/predict')
def predict_premium(data: UserInput, persist: Annotated[bool, Query()] = True):
    # Prepare data for model
    # Note: data.bmi, data.age_group, data.lifestyle_risk, and data.city_tier 
    # are calculated automatically by the @computed_field decorators in your UserInput class.
    input_df = pd.DataFrame([{
        'bmi': data.bmi,
        'age_group': data.age_group,
        'lifestyle_risk': data.lifestyle_risk,
        'city_tier': data.city_tier,
        'income_lpa': data.income_lpa,
        'occupation': data.occupation
    }])

    # Get prediction from pickle model
    prediction = model.predict(input_df)[0]
    risk_segment = normalize_risk_label(prediction)
    probability_payload = get_probability_payload(model, input_df, prediction)
    contributions = shap_contributions(model, input_df, prediction)
    contribution_method = "SHAP" if contributions else "Business Rules"
    if contributions is None:
        contributions = business_rule_contributions(data)

    response_payload = {
        "predicted_category": str(prediction),
        "risk_segment": risk_segment,
        "probability": probability_payload["probability"],
        "confidence": probability_payload["confidence"],
        "confidence_percent": (
            round(probability_payload["confidence"] * 100, 2)
            if probability_payload["confidence"] is not None
            else None
        ),
        "risk_score": probability_payload["risk_score"],
        "risk_level": risk_segment,
        "class_probabilities": probability_payload["class_probabilities"],
        "explanations": generate_explanations(data),
        "feature_contributions": contributions,
        "contribution_method": contribution_method,
        "risk_drivers": rank_risk_drivers(contributions),
        "recommendations": generate_recommendations(data),
        "derived_features": {
            "bmi": round(float(data.bmi), 2),
            "age_group": data.age_group,
            "lifestyle_risk": data.lifestyle_risk,
            "city_tier": data.city_tier,
        },
    }

    if persist:
        history_store.append(data, response_payload)

    # Return nested dictionary to match frontend logic exactly
    return {
        "response": response_payload
    }


@app.get('/history')
def prediction_history(limit: Annotated[int, Query(gt=0, le=5000)] = 500):
    return {
        "records": history_store.records(limit=limit)
    }


@app.get('/analytics/summary')
def analytics_summary():
    return history_store.analytics_summary()
