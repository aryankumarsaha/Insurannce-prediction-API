import streamlit as st
import requests

# streamlit run frontend.py

# Local API URL (Ensure this matches your Uvicorn port)
API_URL = "http://127.0.0.1:8000/predict"

st.set_page_config(page_title="Insurance Predictor", layout="centered")
st.title("🛡️ Insurance Premium Category Predictor")
st.markdown("Fill in the details below to estimate the insurance risk category.")

# Organized input layout using columns for better UI
col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", min_value=1, max_value=119, value=30)
    weight = st.number_input("Weight (kg)", min_value=1.0, value=65.0)
    height = st.number_input("Height (m)", min_value=0.5, max_value=2.5, value=1.70)

with col2:
    income_lpa = st.number_input("Annual Income (LPA)", min_value=0.1, value=10.0)
    smoker = st.selectbox("Are you a smoker?", options=[True, False])
    city = st.text_input("City", value="Mumbai")

occupation = st.selectbox(
    "Occupation",
    ['retired', 'freelancer', 'student', 'government_job', 'business_owner', 'unemployed', 'private_job']
)

st.divider()

if st.button("Predict Premium Category", use_container_width=True):
    # Map inputs to JSON structure expected by FastAPI
    input_data = {
        "age": age,
        "weight": weight,
        "height": height,
        "income_lpa": income_lpa,
        "smoker": smoker,
        "city": city,
        "occupation": occupation
    }

    try:
        with st.spinner('Contacting FastAPI server...'):
            response = requests.post(API_URL, json=input_data)
            result = response.json()

        # Check for success and existence of 'response' key
        if response.status_code == 200 and "response" in result:
            prediction = result["response"]
            
            st.success(f"### Predicted Category: **{prediction['predicted_category']}**")
            
            # Show secondary metrics provided by API
            st.write(f"🔍 **Confidence Score:** {prediction.get('confidence', 'N/A')}")
            if prediction.get("class_probabilities"):
                st.write("📊 **Class Probabilities:**")
                st.json(prediction["class_probabilities"])
        else:
            st.error(f"Error {response.status_code}: Could not retrieve prediction.")
            st.write("Raw API Output:", result)

    except requests.exceptions.ConnectionError:
        st.error("❌ Connection Error: Ensure FastAPI is running on http://127.0.0.1:8000")