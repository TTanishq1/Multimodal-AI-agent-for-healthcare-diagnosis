"""
SQLite history helper for patient visits.

This module is intentionally tiny and synchronous. It stores the raw fusion
result (including any raw LLM output) for basic auditing and can return a
one‑line summary of prior visits for prompt conditioning.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


DB_PATH = Path(os.getenv("PATIENT_HISTORY_DB", "patient_history.db"))


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            timestamp TEXT,
            transcript TEXT,
            image_summary TEXT,
            fusion_result_json TEXT
        )
        """
    )
    return conn


def save_visit(
    patient_id: Optional[str],
    transcript: str,
    image_summary: str,
    fusion_result: Dict[str, Any],
    timestamp: str,
) -> None:
    """Persist a single visit including the raw fusion / LLM output."""
    conn = _get_conn()
    with conn:
        conn.execute(
            """
            INSERT INTO visits (patient_id, timestamp, transcript, image_summary, fusion_result_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                patient_id or "anonymous",
                timestamp,
                transcript or "",
                image_summary or "",
                json.dumps(fusion_result or {}),
            ),
        )
    conn.close()


def get_history_summary(patient_id: Optional[str]) -> str:
    """
    Return a very short one‑line summary of prior visits for this patient.

    This intentionally keeps formatting simple and bounded so it can be
    safely inserted into prompts.
    """
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            SELECT fusion_result_json, timestamp
            FROM visits
            WHERE patient_id = ?
            ORDER BY id DESC
            LIMIT 3
            """,
            (patient_id or "anonymous",),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return "No significant prior history is recorded for this patient."

    diagnoses = []
    for fusion_json, ts in rows:
        try:
            data = json.loads(fusion_json or "{}")
        except json.JSONDecodeError:
            data = {}
        diag = data.get("preliminary_diagnosis") or "unspecified issue"
        diagnoses.append(f"{diag} ({ts})")

    summary = "; ".join(diagnoses)
    return f"Previous visits suggest: {summary}"


