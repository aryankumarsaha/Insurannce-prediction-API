from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


RISK_COLORS = {
    "Low Risk": "#2f9e44",
    "Medium Risk": "#f08c00",
    "High Risk": "#e03131",
}


def risk_gauge(score: int) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 32}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#1f2937"},
                "steps": [
                    {"range": [0, 33], "color": "#d3f9d8"},
                    {"range": [34, 66], "color": "#fff3bf"},
                    {"range": [67, 100], "color": "#ffe3e3"},
                ],
                "threshold": {
                    "line": {"color": "#111827", "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=25, b=10))
    return fig


def contribution_bar(contributions: list[dict]) -> go.Figure:
    df = pd.DataFrame(contributions)
    if df.empty:
        return go.Figure()
    df = df.sort_values("impact", ascending=True)
    fig = px.bar(
        df,
        x="impact",
        y="feature",
        orientation="h",
        color="direction",
        color_discrete_map={
            "Increased Risk": "#e03131",
            "Reduced Risk": "#2f9e44",
            "Neutral": "#6b7280",
        },
        hover_data=["value"],
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10), yaxis_title=None)
    return fig


def driver_ranking(contributions: list[dict]) -> go.Figure:
    df = pd.DataFrame(contributions)
    if df.empty:
        return go.Figure()
    df = df.sort_values("impact", key=lambda series: series.abs(), ascending=True)
    fig = px.bar(
        df,
        x=df["impact"].abs(),
        y="feature",
        orientation="h",
        color="direction",
        color_discrete_map={
            "Increased Risk": "#e03131",
            "Reduced Risk": "#2f9e44",
            "Neutral": "#6b7280",
        },
        labels={"x": "Influence", "feature": ""},
    )
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
    return fig


def risk_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.pie(
        df,
        names="risk_segment",
        color="risk_segment",
        color_discrete_map=RISK_COLORS,
        hole=0.45,
    )
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10))
    return fig


def risk_by_occupation(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby(["occupation", "risk_segment"]).size().reset_index(name="count")
    fig = px.bar(
        grouped,
        x="occupation",
        y="count",
        color="risk_segment",
        color_discrete_map=RISK_COLORS,
        barmode="group",
    )
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10), xaxis_title=None)
    return fig


def risk_by_city_tier(df: pd.DataFrame) -> go.Figure:
    grouped = df.groupby(["city_tier", "risk_segment"]).size().reset_index(name="count")
    fig = px.bar(
        grouped,
        x="city_tier",
        y="count",
        color="risk_segment",
        color_discrete_map=RISK_COLORS,
        barmode="group",
    )
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="City Tier")
    return fig


def income_vs_risk(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="income_lpa",
        y="risk_score",
        color="risk_segment",
        size="bmi",
        hover_data=["age", "occupation", "city", "confidence"],
        color_discrete_map=RISK_COLORS,
    )
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Income LPA")
    return fig


def bmi_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(df, x="bmi", color="risk_segment", color_discrete_map=RISK_COLORS, nbins=20)
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="BMI")
    return fig


def correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    numeric = df[["age", "bmi", "income_lpa", "city_tier", "confidence", "risk_score"]].copy()
    corr = numeric.corr(numeric_only=True).fillna(0)
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10))
    return fig
