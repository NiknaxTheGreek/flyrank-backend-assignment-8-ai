from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import database_path


SEED_RECORDS = [
    ("INV-1001", "Analytics", "Northstar Labs", "North", 1850.00, "2026-07-02"),
    ("INV-1002", "Analytics", "Juniper Works", "West", 1320.50, "2026-07-04"),
    ("INV-1003", "Platform", "Cedar & Co.", "East", 2450.00, "2026-07-08"),
    ("INV-1004", "Platform", "Aster Studio", "South", 2180.00, "2026-07-11"),
    ("INV-1005", "Support", "Mosaic Health", "West", 760.25, "2026-07-14"),
    ("INV-1006", "Support", "Northstar Labs", "North", 980.00, "2026-07-16"),
    ("INV-1007", "Analytics", "River City Foods", "South", 1105.75, "2026-07-19"),
    ("INV-1008", "Platform", "Juniper Works", "West", 3190.00, "2026-07-22"),
    ("INV-1009", "Support", "Cedar & Co.", "East", 895.50, "2026-07-24"),
    ("INV-1010", "Analytics", "Aster Studio", "South", 1560.00, "2026-07-27"),
    ("INV-1011", "Platform", "Mosaic Health", "West", 2725.00, "2026-07-29"),
    ("INV-1012", "Support", "River City Foods", "North", 640.00, "2026-07-31"),
]


def now() -> str:
    return datetime.now(UTC).isoformat()


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_records (
              id TEXT PRIMARY KEY,
              category TEXT NOT NULL,
              customer TEXT NOT NULL,
              region TEXT NOT NULL,
              amount REAL NOT NULL CHECK(amount >= 0),
              recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS report_jobs (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
              delay_seconds REAL NOT NULL DEFAULT 0,
              simulate_failure INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              started_at TEXT,
              completed_at TEXT,
              artifact_reference TEXT,
              error_message TEXT,
              source_record_count INTEGER NOT NULL
            );
            """
        )
        record_count = connection.execute("SELECT COUNT(*) FROM source_records").fetchone()[0]
        if record_count == 0:
            connection.executemany(
                """
                INSERT INTO source_records (id, category, customer, region, amount, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                SEED_RECORDS,
            )


def row_as_job(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    job = dict(row)
    job["simulate_failure"] = bool(job.pop("simulate_failure"))
    return job


def create_job(title: str, delay_seconds: float, simulate_failure: bool) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    timestamp = now()
    with connect() as connection:
        source_count = connection.execute("SELECT COUNT(*) FROM source_records").fetchone()[0]
        connection.execute(
            """
            INSERT INTO report_jobs (
              id, title, status, delay_seconds, simulate_failure, created_at, updated_at, source_record_count
            ) VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)
            """,
            (job_id, title, delay_seconds, int(simulate_failure), timestamp, timestamp, source_count),
        )
        return row_as_job(
            connection.execute("SELECT * FROM report_jobs WHERE id = ?", (job_id,)).fetchone()
        )  # type: ignore[return-value]


def get_job(job_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        return row_as_job(connection.execute("SELECT * FROM report_jobs WHERE id = ?", (job_id,)).fetchone())


def list_jobs() -> list[dict[str, Any]]:
    with connect() as connection:
        return [
            row_as_job(row)  # type: ignore[misc]
            for row in connection.execute("SELECT * FROM report_jobs ORDER BY created_at DESC")
        ]


def claim_next_job() -> dict[str, Any] | None:
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM report_jobs WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if row is None:
            connection.commit()
            return None
        timestamp = now()
        connection.execute(
            """
            UPDATE report_jobs
            SET status = 'running', started_at = ?, updated_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (timestamp, timestamp, row["id"]),
        )
        connection.commit()
        return get_job(str(row["id"]))


def complete_job(job_id: str, artifact_reference: str) -> None:
    timestamp = now()
    with connect() as connection:
        connection.execute(
            """
            UPDATE report_jobs
            SET status = 'completed', artifact_reference = ?, completed_at = ?, updated_at = ?, error_message = NULL
            WHERE id = ? AND status = 'running'
            """,
            (artifact_reference, timestamp, timestamp, job_id),
        )


def fail_job(job_id: str, error_message: str) -> None:
    with connect() as connection:
        connection.execute(
            """
            UPDATE report_jobs
            SET status = 'failed', artifact_reference = NULL, error_message = ?, updated_at = ?
            WHERE id = ? AND status IN ('pending', 'running')
            """,
            (error_message[:500], now(), job_id),
        )


def fetch_source_records() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, category, customer, region, amount, recorded_at
            FROM source_records
            ORDER BY recorded_at ASC, id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def source_summary(records: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    source = list(records) if records is not None else fetch_source_records()
    totals: dict[str, float] = {}
    total_amount = 0.0
    for record in source:
        amount = float(record["amount"])
        total_amount += amount
        totals[record["category"]] = totals.get(record["category"], 0.0) + amount
    return {
        "record_count": len(source),
        "total_amount": round(total_amount, 2),
        "average_amount": round(total_amount / len(source), 2) if source else 0.0,
        "category_totals": {key: round(value, 2) for key, value in sorted(totals.items())},
    }


def artifact_path(reference: str) -> Path:
    from .config import reports_dir

    if Path(reference).name != reference or not reference.endswith(".pdf"):
        raise ValueError("Invalid artifact reference")
    return reports_dir() / reference