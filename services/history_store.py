from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PREDICTION_COLUMNS = [
    "timestamp",
    "age",
    "weight",
    "height",
    "bmi",
    "smoker",
    "city",
    "city_tier",
    "occupation",
    "income_lpa",
    "risk_segment",
    "confidence",
    "risk_score",
]

PREDICTION_SCHEMA = {
    "timestamp": "TEXT NOT NULL DEFAULT ''",
    "age": "INTEGER NOT NULL DEFAULT 0",
    "weight": "REAL NOT NULL DEFAULT 0",
    "height": "REAL NOT NULL DEFAULT 0",
    "bmi": "REAL NOT NULL DEFAULT 0",
    "smoker": "INTEGER NOT NULL DEFAULT 0",
    "city": "TEXT NOT NULL DEFAULT ''",
    "city_tier": "INTEGER NOT NULL DEFAULT 3",
    "occupation": "TEXT NOT NULL DEFAULT ''",
    "income_lpa": "REAL NOT NULL DEFAULT 0",
    "risk_segment": "TEXT NOT NULL DEFAULT ''",
    "confidence": "REAL",
    "risk_score": "INTEGER NOT NULL DEFAULT 0",
}


class PredictionHistoryStore:
    """SQLite repository for prediction history and analytics aggregates."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
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
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_predictions_risk_segment ON predictions(risk_segment)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_predictions_occupation ON predictions(occupation)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_predictions_city_tier ON predictions(city_tier)"
                )
                self._migrate_predictions_table(connection)

    def append(self, data: Any, response: dict[str, Any]) -> None:
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "age": int(data.age),
            "weight": float(data.weight),
            "height": float(data.height),
            "bmi": round(float(data.bmi), 2),
            "smoker": int(bool(data.smoker)),
            "city": str(data.city).strip(),
            "city_tier": int(data.city_tier),
            "occupation": str(data.occupation),
            "income_lpa": float(data.income_lpa),
            "risk_segment": response["risk_segment"],
            "confidence": response.get("confidence"),
            "risk_score": int(response.get("risk_score", 0)),
        }

        placeholders = ", ".join("?" for _ in PREDICTION_COLUMNS)
        columns = ", ".join(PREDICTION_COLUMNS)
        values = [row[column] for column in PREDICTION_COLUMNS]

        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    f"INSERT INTO predictions ({columns}) VALUES ({placeholders})",
                    values,
                )

    def records(self, limit: int = 500) -> list[dict[str, Any]]:
        query = """
            SELECT timestamp, age, weight, height, bmi, smoker, city, city_tier,
                   occupation, income_lpa, risk_segment, confidence, risk_score
            FROM predictions
            ORDER BY timestamp DESC
            LIMIT ?
        """
        records = self._fetch_all(query, [limit])
        return self._convert_smoker_to_bool(records)

    def analytics_summary(self) -> dict[str, Any]:
        return {
            "kpis": self._kpis(),
            "risk_distribution": self.risk_distribution(),
            "occupation_analysis": self.occupation_analysis(),
            "city_tier_analysis": self.city_tier_analysis(),
            "income_analysis": self.income_analysis(),
            "trend_analysis": self.trend_analysis(),
        }

    def risk_distribution(self) -> list[dict[str, Any]]:
        records = self._fetch_all(
            """
            SELECT risk_segment, COUNT(*) AS prediction_count,
                   ROUND(AVG(confidence), 4) AS avg_confidence,
                   ROUND(AVG(risk_score), 2) AS avg_risk_score
            FROM predictions
            GROUP BY risk_segment
            ORDER BY prediction_count DESC
            """
        )
        return records

    def occupation_analysis(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT occupation, risk_segment, COUNT(*) AS prediction_count,
                   ROUND(AVG(income_lpa), 2) AS avg_income_lpa,
                   ROUND(AVG(bmi), 2) AS avg_bmi,
                   ROUND(AVG(risk_score), 2) AS avg_risk_score
            FROM predictions
            GROUP BY occupation, risk_segment
            ORDER BY occupation, prediction_count DESC
            """
        )

    def city_tier_analysis(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT city_tier, risk_segment, COUNT(*) AS prediction_count,
                   ROUND(AVG(confidence), 4) AS avg_confidence,
                   ROUND(AVG(risk_score), 2) AS avg_risk_score
            FROM predictions
            GROUP BY city_tier, risk_segment
            ORDER BY city_tier, risk_segment
            """
        )

    def income_analysis(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                CASE
                    WHEN income_lpa < 5 THEN '0-5 LPA'
                    WHEN income_lpa < 10 THEN '5-10 LPA'
                    WHEN income_lpa < 20 THEN '10-20 LPA'
                    WHEN income_lpa < 40 THEN '20-40 LPA'
                    ELSE '40+ LPA'
                END AS income_band,
                risk_segment,
                COUNT(*) AS prediction_count,
                ROUND(AVG(income_lpa), 2) AS avg_income_lpa,
                ROUND(AVG(risk_score), 2) AS avg_risk_score
            FROM predictions
            GROUP BY income_band, risk_segment
            ORDER BY MIN(income_lpa), risk_segment
            """
        )

    def trend_analysis(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT DATE(timestamp) AS prediction_date, risk_segment,
                   COUNT(*) AS prediction_count,
                   ROUND(AVG(confidence), 4) AS avg_confidence,
                   ROUND(AVG(risk_score), 2) AS avg_risk_score
            FROM predictions
            GROUP BY DATE(timestamp), risk_segment
            ORDER BY prediction_date, risk_segment
            """
        )

    def _kpis(self) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT COUNT(*) AS total_predictions,
                   ROUND(AVG(confidence), 4) AS avg_confidence,
                   ROUND(AVG(risk_score), 2) AS avg_risk_score,
                   ROUND(AVG(CASE WHEN risk_segment = 'High Risk' THEN 1.0 ELSE 0.0 END), 4)
                       AS high_risk_share
            FROM predictions
            """
        )
        return rows[0] if rows else {}

    def _fetch_all(self, query: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            cursor = connection.execute(query, params or [])
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def _migrate_predictions_table(self, connection: sqlite3.Connection) -> None:
        """Migrate predictions table schema: detect missing columns and add them.
        
        Uses PRAGMA table_info to detect the existing schema and automatically
        adds missing columns with their default values. Maintains backward
        compatibility with existing databases.
        """
        try:
            existing_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(predictions)").fetchall()
            }
            for column, column_type in PREDICTION_SCHEMA.items():
                if column not in existing_columns:
                    connection.execute(
                        f"ALTER TABLE predictions ADD COLUMN {column} {column_type}"
                    )
        except sqlite3.Error as e:
            # Log migration attempt but don't fail initialization if table doesn't exist
            # (it will be created by the CREATE TABLE IF NOT EXISTS statement)
            pass

    def _convert_smoker_to_bool(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert smoker field from integer (0/1) to boolean for API consistency."""
        for record in records:
            if "smoker" in record:
                record["smoker"] = bool(record["smoker"])
        return records

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
