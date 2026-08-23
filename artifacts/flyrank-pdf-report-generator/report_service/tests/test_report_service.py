from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from report_service.api import app
from report_service.database import artifact_path, get_job, initialize_database, source_summary
from report_service.worker import process_one


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPORT_DB_PATH", str(tmp_path / "reports.sqlite3"))
    monkeypatch.setenv("REPORT_OUTPUT_DIR", str(tmp_path / "reports"))
    initialize_database()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_request_acceptance_and_invalid_input(client: TestClient) -> None:
    rejected = client.post("/api/reports", json={"title": "x"})
    assert rejected.status_code == 422
    accepted = client.post("/api/reports", json={"title": "July performance", "delay_seconds": 0})
    assert accepted.status_code == 202
    assert accepted.json()["status"] == "pending"


def test_background_contract_and_state_transition(client: TestClient) -> None:
    job = client.post("/api/reports", json={"title": "Async proof", "delay_seconds": 0}).json()
    assert client.get(f"/api/reports/{job['id']}").json()["status"] == "pending"
    assert process_one() is True
    completed = client.get(f"/api/reports/{job['id']}").json()
    assert completed["status"] == "completed"
    assert completed["artifact_reference"]


def test_successful_pdf_generation_and_data_integrity(client: TestClient) -> None:
    job = client.post("/api/reports", json={"title": "Integrity report", "delay_seconds": 0}).json()
    process_one()
    response = client.get(f"/api/reports/{job['id']}/result")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    path = artifact_path(get_job(job["id"])["artifact_reference"])  # type: ignore[index]
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    summary = source_summary()
    assert f"Records processed: {summary['record_count']}" in text
    assert f"Total amount: ${summary['total_amount']:,.2f}" in text


def test_regression_report_keeps_aggregate_and_detailed_records(client: TestClient) -> None:
    job = client.post("/api/reports", json={"title": "Regression report", "delay_seconds": 0}).json()
    process_one()
    path = artifact_path(get_job(job["id"])["artifact_reference"])  # type: ignore[index]
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    assert "Executive aggregate" in text
    assert "Detailed source records" in text
    assert "INV-1001" in text
    assert "INV-1012" in text


def test_multiple_jobs_have_unique_artifacts(client: TestClient) -> None:
    first = client.post("/api/reports", json={"title": "First report", "delay_seconds": 0}).json()
    second = client.post("/api/reports", json={"title": "Second report", "delay_seconds": 0}).json()
    process_one()
    process_one()
    first_reference = get_job(first["id"])["artifact_reference"]  # type: ignore[index]
    second_reference = get_job(second["id"])["artifact_reference"]  # type: ignore[index]
    assert first_reference and second_reference and first_reference != second_reference


def test_controlled_failure_never_exposes_partial_pdf(client: TestClient) -> None:
    job = client.post(
        "/api/reports", json={"title": "Failure report", "delay_seconds": 0, "simulate_failure": True}
    ).json()
    process_one()
    failed = client.get(f"/api/reports/{job['id']}").json()
    assert failed["status"] == "failed"
    assert failed["artifact_reference"] is None
    assert client.get(f"/api/reports/{job['id']}/result").status_code == 409
    reports = Path(os.environ["REPORT_OUTPUT_DIR"])
    assert not list(reports.glob("*.pdf"))
    assert not list(reports.glob("*.partial"))


def test_missing_job_and_source_aggregation(client: TestClient) -> None:
    assert client.get("/api/reports/not-real").status_code == 404
    payload = client.get("/api/source-summary").json()
    assert payload == {
        "record_count": 12,
        "total_amount": 19657.0,
        "average_amount": 1638.08,
        "category_totals": {"Analytics": 5836.25, "Platform": 10545.0, "Support": 3275.75},
    }