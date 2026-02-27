# 🛡️ Insurance Premium Category Predictor

This project is a machine learning-based Insurance Premium Category Predictor that utilizes a **FastAPI** backend for predictions and a **Streamlit** frontend for user interaction. The entire application is containerized using **Docker** for easy deployment.

## 🚀 Features
* **FastAPI Backend:** Provides robust API endpoints for insurance risk assessment.
* **Streamlit Frontend:** A clean, responsive user interface to input user details.
* **Dockerized:** A single-container deployment running both the API and the UI.
* **Data Validation:** Uses Pydantic for input validation and automatic BMI/age group/city-tier calculations.

## 📂 Project Structure
```text
.
├── app.py              # FastAPI backend
├── frontend.py         # Streamlit frontend
├── model.pkl           # Trained ML model
├── Dockerfile          # Container configuration
├── requirements.txt    # Project dependencies
├── config/             # Configuration modules
└── schema/             # Data validation schemas

🛠️ Installation & Setup
Local Development
Clone the repository.

Install dependencies:

Bash
pip install -r requirements.txt
Run the backend:

Bash
uvicorn app:app --reload
Run the frontend (in a separate terminal):

Bash
streamlit run frontend.py
Docker Deployment
Build the image:

Bash
docker build -t aryankumarsaha/insurance-app .
Run the container:

Bash
docker run -p 8000:8000 -p 8501:8501 aryankumarsaha/insurance-app
Access the app at http://localhost:8501.

📡 API Endpoints
GET /: Health check and API status.

POST /predict: Sends user data and receives a premium category prediction.