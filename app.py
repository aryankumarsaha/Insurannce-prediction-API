

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from schema.user_input import UserInput
from config.city_tier import tier_2_cities, tier_1_cities
from typing import Literal, Annotated
import pickle
import pandas as pd


# uvicorn app:app --reload
# streamlit run frontend.py

# ML flow metadata
MODEL_VERSION = '1.0.0'

# Load the ml model
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

app = FastAPI()

@app.get('/')
def home():
    return {'msg': 'Insurance prediction API'}

@app.get('/health')
def health_check():
    return {
        'status': "ok",
        "version": MODEL_VERSION,
        'model_loaded': model is not None
    }

@app.post('/predict')
def predict_premium(data: UserInput):
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

    # Return nested dictionary to match frontend logic exactly
    return {
        "response": {
            "predicted_category": str(prediction),
            "confidence": "N/A",
            "class_probabilities": {}
        }
    }

#
