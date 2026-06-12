# Enterprise Explainable AI Insurance Risk Assessment Dashboard

## Architecture

FastAPI remains the prediction source of truth. Streamlit sends applicant data to `/predict`, FastAPI derives model features, calls the existing scikit-learn pipeline, enriches the response with explainability, and persists production analytics records into SQLite.

```text
Streamlit UI
  -> FastAPI /predict
      -> UserInput validation
      -> Derived features
      -> model.pkl sklearn Pipeline
      -> predict + predict_proba
      -> explainability payload
      -> SQLite predictions table
  -> FastAPI /history
  -> FastAPI /analytics/summary
  -> Tableau iframe embed
```

## Updated Folder Structure

```text
.
├── app.py
├── frontend.py
├── model.pkl
├── requirements.txt
├── DASHBOARD_README.md
├── analytics/
│   ├── __init__.py
│   └── tableau_embed.py
├── dashboard/
│   ├── __init__.py
│   ├── api_client.py
│   ├── charts.py
│   └── styles.py
├── services/
│   ├── __init__.py
│   ├── history_store.py
│   └── risk_engine.py
├── schema/
│   └── user_input.py
├── config/
│   └── city_tier.py
└── data/
    └── insurance_predictions.db
```

`data/insurance_predictions.db` is created automatically on application startup.

## SQLite Analytics Schema

Table: `predictions`

```sql
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    age INTEGER NOT NULL,
    weight REAL NOT NULL,
    height REAL NOT NULL,
    bmi REAL NOT NULL,
    smoker INTEGER NOT NULL,
    city TEXT NOT NULL,
    city_tier INTEGER NOT NULL,
    occupation TEXT NOT NULL,
    income_lpa REAL NOT NULL,
    risk_segment TEXT NOT NULL,
    confidence REAL,
    risk_score INTEGER NOT NULL
);
```

Indexes are created for `timestamp`, `risk_segment`, `occupation`, and `city_tier`.

## API Endpoints

### `POST /predict`

Preserves the existing ML functionality and response nesting:

```json
{
  "response": {
    "predicted_category": "High",
    "risk_segment": "High Risk",
    "confidence": 0.87,
    "confidence_percent": 87.0,
    "risk_score": 78
  }
}
```

Query parameter:

- `persist=true`: stores the prediction in SQLite.
- `persist=false`: used by the What If simulator so scenarios do not pollute production history.

### `GET /history`

Returns raw prediction records from SQLite.

### `GET /analytics/summary`

Returns Tableau-ready aggregation payloads:

- `risk_distribution`
- `occupation_analysis`
- `city_tier_analysis`
- `income_analysis`
- `trend_analysis`

## Tableau Integration

Module:

```text
analytics/tableau_embed.py
```

Configuration:

```bash
set TABLEAU_DASHBOARD_URL=https://public.tableau.com/views/your-dashboard
```

Streamlit embeds the dashboard using:

```python
streamlit.components.v1.iframe
```

If no Tableau URL is configured, the Tableau Analytics tab shows native Plotly analytics sourced from SQLite and exposes the same aggregation tables used for BI integration.

## Tableau Aggregation Queries

Risk distribution:

```sql
SELECT risk_segment, COUNT(*) AS prediction_count,
       ROUND(AVG(confidence), 4) AS avg_confidence,
       ROUND(AVG(risk_score), 2) AS avg_risk_score
FROM predictions
GROUP BY risk_segment;
```

Occupation analysis:

```sql
SELECT occupation, risk_segment, COUNT(*) AS prediction_count,
       ROUND(AVG(income_lpa), 2) AS avg_income_lpa,
       ROUND(AVG(bmi), 2) AS avg_bmi,
       ROUND(AVG(risk_score), 2) AS avg_risk_score
FROM predictions
GROUP BY occupation, risk_segment;
```

City tier analysis:

```sql
SELECT city_tier, risk_segment, COUNT(*) AS prediction_count,
       ROUND(AVG(confidence), 4) AS avg_confidence,
       ROUND(AVG(risk_score), 2) AS avg_risk_score
FROM predictions
GROUP BY city_tier, risk_segment;
```

Income analysis:

```sql
SELECT income_band, risk_segment, COUNT(*) AS prediction_count,
       AVG(income_lpa) AS avg_income_lpa,
       AVG(risk_score) AS avg_risk_score
FROM income_banded_predictions
GROUP BY income_band, risk_segment;
```

Trend analysis:

```sql
SELECT DATE(timestamp) AS prediction_date, risk_segment,
       COUNT(*) AS prediction_count,
       AVG(confidence) AS avg_confidence,
       AVG(risk_score) AS avg_risk_score
FROM predictions
GROUP BY DATE(timestamp), risk_segment;
```

## Setup

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

In a second terminal:

```bash
streamlit run frontend.py
```

Optional Tableau configuration:

```bash
set TABLEAU_DASHBOARD_URL=https://public.tableau.com/views/your-dashboard
streamlit run frontend.py
```
