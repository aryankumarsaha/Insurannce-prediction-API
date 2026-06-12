from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        .kpi-card {
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 18px 18px 14px 18px;
            background: #ffffff;
            min-height: 118px;
        }
        .kpi-label {
            color: #4b5563;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 8px;
        }
        .kpi-value {
            color: #111827;
            font-size: 1.7rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .risk-badge {
            display: inline-block;
            border-radius: 6px;
            padding: 6px 10px;
            font-weight: 700;
            color: #ffffff;
            margin-top: 8px;
        }
        .badge-low { background: #2f9e44; }
        .badge-medium { background: #f08c00; }
        .badge-high { background: #e03131; }
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin: 0.4rem 0 0.8rem 0;
            color: #111827;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, badge: str | None = None) -> None:
    badge_html = ""
    if badge:
        badge_class = "badge-low"
        if "Medium" in badge:
            badge_class = "badge-medium"
        if "High" in badge:
            badge_class = "badge-high"
        badge_html = f'<div class="risk-badge {badge_class}">{badge}</div>'

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
