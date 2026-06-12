from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

from analytics.tableau_embed import get_tableau_dashboard_url, render_tableau_dashboard
from dashboard.api_client import ApiClient
from dashboard.charts import (
    bmi_histogram,
    contribution_bar,
    correlation_heatmap,
    driver_ranking,
    income_vs_risk,
    risk_by_city_tier,
    risk_by_occupation,
    risk_distribution,
    risk_gauge,
)
from dashboard.styles import apply_theme, kpi_card


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")
OCCUPATIONS = [
    "retired",
    "freelancer",
    "student",
    "government_job",
    "business_owner",
    "unemployed",
    "private_job",
]


def main() -> None:
    st.set_page_config(page_title="Insurance Risk Assessment", layout="wide")
    apply_theme()

    client = ApiClient(API_BASE_URL)
    st.title("Explainable AI Insurance Risk Assessment Dashboard")
    st.caption("FastAPI prediction service with Streamlit business intelligence views")

    with st.sidebar:
        st.header("Applicant Inputs")
        payload = input_panel()
        predict_clicked = st.button("Run Risk Assessment", use_container_width=True, type="primary")
        st.divider()
        api_status(client)

    if "current_payload" not in st.session_state:
        st.session_state.current_payload = payload
    if "current_prediction" not in st.session_state:
        st.session_state.current_prediction = None

    if predict_clicked:
        run_prediction(client, payload, persist=True)

    tab_prediction, tab_explain, tab_what_if, tab_history, tab_tableau = st.tabs(
        [
            "Prediction",
            "Explainability",
            "What If Analysis",
            "History",
            "Tableau Analytics",
        ]
    )

    with tab_prediction:
        prediction_page()

    with tab_explain:
        explainability_page()

    with tab_what_if:
        what_if_page(client)

    with tab_history:
        history_page(client)

    with tab_tableau:
        tableau_analytics_page(client)


def input_panel() -> dict[str, Any]:
    age = st.number_input("Age", min_value=1, max_value=119, value=30)
    weight = st.number_input("Weight (kg)", min_value=1.0, value=65.0)
    height = st.number_input("Height (m)", min_value=0.5, max_value=2.49, value=1.70)
    income_lpa = st.number_input("Annual Income (LPA)", min_value=0.1, value=10.0)
    smoker = st.toggle("Smoker", value=False)
    city = st.text_input("City", value="Mumbai")
    occupation = st.selectbox("Occupation", OCCUPATIONS, index=OCCUPATIONS.index("private_job"))

    return {
        "age": int(age),
        "weight": float(weight),
        "height": float(height),
        "income_lpa": float(income_lpa),
        "smoker": bool(smoker),
        "city": city,
        "occupation": occupation,
    }


def api_status(client: ApiClient) -> None:
    try:
        health = client.health()
        st.success(f"API online | Model {health.get('version', 'unknown')}")
    except requests.RequestException:
        st.error(f"API offline at {API_BASE_URL}")


def run_prediction(client: ApiClient, payload: dict[str, Any], persist: bool) -> dict[str, Any] | None:
    try:
        prediction = client.predict(payload, persist=persist)
        if persist:
            st.session_state.current_payload = payload
            st.session_state.current_prediction = prediction
        return prediction
    except requests.RequestException as exc:
        st.error(f"Prediction service error: {exc}")
        return None


def prediction_page() -> None:
    prediction = st.session_state.current_prediction
    if not prediction:
        st.info("Run a risk assessment from the sidebar to populate the executive dashboard.")
        return

    risk_segment = prediction["risk_segment"]
    confidence = prediction.get("confidence_percent")
    confidence_display = f"{confidence:.1f}%" if confidence is not None else "N/A"
    risk_score = int(prediction.get("risk_score", 0))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Predicted Segment", risk_segment.upper(), risk_segment)
    with col2:
        kpi_card("Confidence Score", confidence_display)
    with col3:
        kpi_card("Risk Score", f"{risk_score}/100")
    with col4:
        kpi_card("Lifestyle Risk", prediction["derived_features"]["lifestyle_risk"].title())

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown('<div class="section-title">Risk Gauge</div>', unsafe_allow_html=True)
        st.plotly_chart(risk_gauge(risk_score), use_container_width=True, key="prediction_risk_gauge")
    with right:
        st.markdown('<div class="section-title">Class Probabilities</div>', unsafe_allow_html=True)
        probabilities = prediction.get("class_probabilities", {})
        if probabilities:
            probability_df = pd.DataFrame(
                [{"Segment": key, "Probability": value} for key, value in probabilities.items()]
            )
            st.dataframe(
                probability_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Probability": st.column_config.ProgressColumn(
                        format="%.1f",
                        min_value=0,
                        max_value=1,
                    )
                },
            )
        else:
            st.info("The current model response does not include class probabilities.")

    st.markdown('<div class="section-title">Recommendation Engine</div>', unsafe_allow_html=True)
    rec_cols = st.columns(3)
    for index, recommendation in enumerate(prediction.get("recommendations", [])):
        with rec_cols[index % 3]:
            st.info(recommendation)


def explainability_page() -> None:
    prediction = st.session_state.current_prediction
    if not prediction:
        st.info("Run a prediction first to see explainability details.")
        return

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="section-title">Why This Prediction?</div>', unsafe_allow_html=True)
        for explanation in prediction.get("explanations", []):
            st.write(f"- {explanation}")

        st.markdown('<div class="section-title">Feature Contribution Table</div>', unsafe_allow_html=True)
        st.caption(f"Contribution method: {prediction.get('contribution_method', 'Business Rules')}")
        st.dataframe(pd.DataFrame(prediction.get("feature_contributions", [])), use_container_width=True, hide_index=True)

    with right:
        st.markdown('<div class="section-title">Feature Contribution Analysis</div>', unsafe_allow_html=True)
        st.plotly_chart(contribution_bar(prediction.get("feature_contributions", [])), use_container_width=True, key="contribution_bar")

    st.markdown('<div class="section-title">Risk Driver Ranking</div>', unsafe_allow_html=True)
    rank_left, rank_right = st.columns([0.8, 1.2])
    with rank_left:
        drivers = prediction.get("risk_drivers", [])
        for driver in drivers[:5]:
            st.metric(
                label=f"{driver['rank']}. {driver['feature']}",
                value=driver["direction"],
                delta=driver["impact"],
            )
    with rank_right:
        st.plotly_chart(driver_ranking(prediction.get("feature_contributions", [])), use_container_width=True, key="driver_ranking")


def what_if_page(client: ApiClient) -> None:
    current_payload = st.session_state.current_payload
    current_prediction = st.session_state.current_prediction
    if not current_prediction:
        st.info("Run a base prediction first, then simulate changes here.")
        return

    st.markdown('<div class="section-title">What-If Simulator</div>', unsafe_allow_html=True)
    current_bmi = current_payload["weight"] / (current_payload["height"] ** 2)

    col1, col2, col3 = st.columns(3)
    with col1:
        target_bmi = st.slider("Scenario BMI", min_value=16.0, max_value=45.0, value=float(round(current_bmi, 1)), step=0.1)
    with col2:
        target_income = st.slider(
            "Scenario Income LPA",
            min_value=0.1,
            max_value=80.0,
            value=float(current_payload["income_lpa"]),
            step=0.5,
        )
    with col3:
        target_smoker = st.toggle("Scenario Smoker", value=bool(current_payload["smoker"]))

    scenario_payload = dict(current_payload)
    scenario_payload["income_lpa"] = target_income
    scenario_payload["smoker"] = target_smoker
    scenario_payload["weight"] = round(target_bmi * (current_payload["height"] ** 2), 2)

    scenario_prediction = run_prediction(client, scenario_payload, persist=False)
    if not scenario_prediction:
        return

    left, right = st.columns(2)
    with left:
        kpi_card(
            "Current Prediction",
            current_prediction["risk_segment"].upper(),
            current_prediction["risk_segment"],
        )
        st.plotly_chart(
            risk_gauge(int(current_prediction["risk_score"])),
            use_container_width=True,
            key="what_if_current_risk_gauge",
        )
    with right:
        kpi_card(
            "Modified Prediction",
            scenario_prediction["risk_segment"].upper(),
            scenario_prediction["risk_segment"],
        )
        st.plotly_chart(
            risk_gauge(int(scenario_prediction["risk_score"])),
            use_container_width=True,
            key="what_if_scenario_risk_gauge",
        )


def history_page(client: ApiClient) -> None:
    df = history_dataframe(client)
    if df.empty:
        st.info("Prediction history is empty.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Total Predictions", str(len(df)))
    with col2:
        kpi_card("Average Confidence", f"{df['confidence'].mean() * 100:.1f}%")
    with col3:
        kpi_card("Average Risk Score", f"{df['risk_score'].mean():.1f}")
    with col4:
        kpi_card("High Risk Share", f"{(df['risk_segment'].eq('High Risk').mean() * 100):.1f}%")

    st.markdown('<div class="section-title">Stored Prediction History</div>', unsafe_allow_html=True)
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)


def tableau_analytics_page(client: ApiClient) -> None:
    st.markdown('<div class="section-title">Tableau Analytics</div>', unsafe_allow_html=True)
    dashboard_url = get_tableau_dashboard_url()
    if dashboard_url:
        render_tableau_dashboard(dashboard_url)
    else:
        st.info("No Tableau dashboard URL configured. Showing native analytics generated from SQLite.")

    summary = analytics_summary(client)
    if summary:
        render_summary_tables(summary)

    df = history_dataframe(client)
    if df.empty:
        st.info("No SQLite prediction records are available yet.")
        return

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.markdown('<div class="section-title">Risk Segment Distribution</div>', unsafe_allow_html=True)
        st.plotly_chart(risk_distribution(df), use_container_width=True, key="tableau_risk_distribution")
    with row1_col2:
        st.markdown('<div class="section-title">Risk by Occupation</div>', unsafe_allow_html=True)
        st.plotly_chart(risk_by_occupation(df), use_container_width=True, key="tableau_risk_by_occupation")

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.markdown('<div class="section-title">Risk by City Tier</div>', unsafe_allow_html=True)
        st.plotly_chart(risk_by_city_tier(df), use_container_width=True, key="tableau_risk_by_city_tier")
    with row2_col2:
        st.markdown('<div class="section-title">Income vs Risk</div>', unsafe_allow_html=True)
        st.plotly_chart(income_vs_risk(df), use_container_width=True, key="tableau_income_vs_risk")

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        st.markdown('<div class="section-title">BMI Distribution</div>', unsafe_allow_html=True)
        st.plotly_chart(bmi_histogram(df), use_container_width=True, key="tableau_bmi_distribution")
    with row3_col2:
        st.markdown('<div class="section-title">Correlation Heatmap</div>', unsafe_allow_html=True)
        st.plotly_chart(correlation_heatmap(df), use_container_width=True, key="tableau_correlation_heatmap")


def analytics_summary(client: ApiClient) -> dict[str, Any]:
    try:
        return client.analytics_summary()
    except requests.RequestException as exc:
        st.error(f"Could not load analytics summary: {exc}")
        return {}


def render_summary_tables(summary: dict[str, Any]) -> None:
    with st.expander("SQLite Aggregations for Tableau", expanded=False):
        sections = [
            ("Risk Distribution", "risk_distribution"),
            ("Occupation Analysis", "occupation_analysis"),
            ("City Tier Analysis", "city_tier_analysis"),
            ("Income Analysis", "income_analysis"),
            ("Trend Analysis", "trend_analysis"),
        ]
        for label, key in sections:
            st.markdown(f"**{label}**")
            st.dataframe(pd.DataFrame(summary.get(key, [])), use_container_width=True, hide_index=True)


def history_dataframe(client: ApiClient) -> pd.DataFrame:
    try:
        records = client.history(limit=5000)
    except requests.RequestException as exc:
        st.error(f"Could not load history: {exc}")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if df.empty:
        return df

    for column in ["age", "bmi", "income_lpa", "city_tier", "confidence", "risk_score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


if __name__ == "__main__":
    main()
