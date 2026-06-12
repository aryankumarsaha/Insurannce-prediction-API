# 🛡️ Insurance Premium Category Predictor

This project is a machine learning-based Insurance Premium Category Predictor that uses a **FastAPI** backend for predictions and a **Streamlit** frontend for user interaction.

## 🚀 Features
- **FastAPI Backend:** Exposes prediction and analytics endpoints.
- **Streamlit Frontend:** Interactive dashboard for risk assessment, explainability, history, and Tableau embedding.
- **SQLite History:** Persists prediction history and analytics to a local database.
- **Tableau Embed Support:** Optional embedded Tableau dashboard via environment variable.

## 📂 Project Structure
```text
.
├── app.py                      # FastAPI backend
├── frontend.py                 # Streamlit frontend
├── model.pkl                   # Trained ML model
├── Dockerfile                  # Container configuration
├── requirements.txt            # Python dependencies
├── analytics/                  # Tableau embed helper
├── config/                     # Configuration modules
├── dashboard/                  # Streamlit charts and UI helpers
├── schema/                     # Pydantic validation schemas
└── services/                   # Prediction history and risk engine
```

## 🛠️ Local Setup
1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Start the FastAPI backend.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

4. Start the Streamlit frontend in a separate terminal.

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend.py
```

5. Open the app in your browser at:

- Streamlit UI: `http://localhost:8501`
- FastAPI docs: `http://localhost:8000/docs`

## 📡 Tableau Integration
To embed a Tableau dashboard, set the `TABLEAU_DASHBOARD_URL` environment variable before running Streamlit.

```powershell
$env:TABLEAU_DASHBOARD_URL = "https://public.tableau.com/views/YourDashboardName/Sheet1"
```

Then restart Streamlit and open the **Tableau Analytics** tab.

If the variable is not set, the app will show native SQLite analytics instead.

## ✅ API Endpoints
- `GET /` — Health check and API status.
- `GET /health` — Model and database status.
- `POST /predict` — Submit user data and receive insurance risk prediction.
- `GET /history` — Retrieve prediction history from SQLite.
- `GET /analytics/summary` — Retrieve analytics summary from history data.

## ⚠️ Notes
- The Tableau dashboard must be created and published separately in Tableau Public, Tableau Online, or Tableau Server.
- This repo does not automatically create a Tableau dashboard for you.
