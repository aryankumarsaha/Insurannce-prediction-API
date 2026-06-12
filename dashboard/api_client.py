from __future__ import annotations

from typing import Any

import requests


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def predict(self, payload: dict[str, Any], persist: bool = True) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/predict",
            params={"persist": str(persist).lower()},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["response"]

    def history(self, limit: int = 1000) -> list[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/history", params={"limit": limit}, timeout=20)
        response.raise_for_status()
        return response.json().get("records", [])

    def analytics_summary(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/analytics/summary", timeout=20)
        response.raise_for_status()
        return response.json()

    def health(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/health", timeout=10)
        response.raise_for_status()
        return response.json()
