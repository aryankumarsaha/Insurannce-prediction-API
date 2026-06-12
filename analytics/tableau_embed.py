from __future__ import annotations

import os

import streamlit as st
import streamlit.components.v1 as components


TABLEAU_DASHBOARD_URL = os.getenv("TABLEAU_DASHBOARD_URL", "").strip()


def get_tableau_dashboard_url() -> str:
    return TABLEAU_DASHBOARD_URL


def render_tableau_dashboard(url: str | None = None, height: int = 820) -> None:
    dashboard_url = (url or get_tableau_dashboard_url()).strip()
    if not dashboard_url:
        st.info("Set TABLEAU_DASHBOARD_URL to embed an enterprise Tableau dashboard here.")
        st.code("set TABLEAU_DASHBOARD_URL=https://public.tableau.com/views/your-dashboard", language="bash")
        return

    components.iframe(
        src=dashboard_url,
        height=height,
        scrolling=True,
    )
