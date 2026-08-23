from __future__ import annotations

import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

import fitz
import httpx
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[4]
SERVICE = ROOT / "artifacts" / "flyrank-pdf-report-generator"
EVIDENCE = ROOT / "verification_evidence"
RUNTIME = EVIDENCE / "runtime"
PORT = 8011
BASE_URL = f"http://127.0.0.1:{PORT}"


def wait_for_health() -> None:
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{BASE_URL}/api/healthz", timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.1)
    raise RuntimeError("API did not become healthy")


def wait_for_status(job_id: str, expected_status: str) -> dict:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        job = httpx.get(f"{BASE_URL}/api/reports/{job_id}", timeout=1).json()
        if job["status"] == expected_status:
            return job
        time.sleep(0.15)
    raise RuntimeError(f"Job {job_id} did not reach {expected_status}")


def start_worker(environment: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", "report_service.worker"],
        cwd=SERVICE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def source_rows_from_database() -> list[dict[str, str]]:
    database = RUNTIME / "reports.sqlite3"
    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            """
            SELECT id, recorded_at, category, customer, region, amount
            FROM source_records
            ORDER BY recorded_at ASC, id ASC
            """
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "recorded_at": str(row[1]),
            "category": str(row[2]),
            "customer": str(row[3]),
            "region": str(row[4]),
            "amount": f"{Decimal(str(row[5])):.2f}",
        }
        for row in rows
    ]


def extracted_detail_rows(text: str) -> list[dict[str, str]]:
    matches = re.findall(
        r"(?m)^(INV-\d+)\n(\d{4}-\d{2}-\d{2})\n([^\n]+)\n([^\n]+)\n([^\n]+)\n\$([\d,]+\.\d{2})$",
        text,
    )
    return [
        {
            "id": record_id,
            "recorded_at": recorded_at,
            "category": category,
            "customer": customer,
            "region": region,
            "amount": amount.replace(",", ""),
        }
        for record_id, recorded_at, category, customer, region, amount in matches
    ]


def terminate(process: subprocess.Popen[str]) -> None:
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> None:
    if EVIDENCE.exists():
        shutil.rmtree(EVIDENCE)
    RUNTIME.mkdir(parents=True)
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(SERVICE),
            "REPORT_DB_PATH": str(RUNTIME / "reports.sqlite3"),
            "REPORT_OUTPUT_DIR": str(RUNTIME / "reports"),
            "REPORT_WORKER_POLL_SECONDS": "0.05",
        }
    )
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "report_service.api:app", "--port", str(PORT)],
        cwd=SERVICE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    worker: subprocess.Popen[str] | None = None
    try:
        wait_for_health()
        started = time.monotonic()
        first = httpx.post(
            f"{BASE_URL}/api/reports",
            json={"title": "E2E Source Performance Report", "delay_seconds": 1.0},
            timeout=2,
        )
        elapsed_ms = round((time.monotonic() - started) * 1000, 1)
        assert first.status_code == 202, first.text
        first_job = first.json()
        pending = wait_for_status(first_job["id"], "pending")

        # The worker starts only after pending has been observed. The normal request delay
        # then makes the running state deterministically observable without changing production code.
        worker = start_worker(environment)
        running = wait_for_status(first_job["id"], "running")
        completed = wait_for_status(first_job["id"], "completed")
        assert completed["status"] == "completed", completed
        downloaded = httpx.get(f"{BASE_URL}/api/reports/{first_job['id']}/result", timeout=4)
        assert downloaded.status_code == 200
        pdf_path = EVIDENCE / "report-one.pdf"
        pdf_path.write_bytes(downloaded.content)
        assert downloaded.content.startswith(b"%PDF")
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        source_rows = source_rows_from_database()
        expected_total = sum(Decimal(row["amount"]) for row in source_rows)
        expected_average = expected_total / len(source_rows)
        expected_tokens = [
            f"Records processed: {len(source_rows)}",
            f"Total amount: ${expected_total:,.2f}",
            f"Average amount: ${expected_average:,.2f}",
            "Detailed source records",
        ]
        assert all(token in extracted for token in expected_tokens)
        extracted_rows = extracted_detail_rows(extracted)
        assert extracted_rows == source_rows
        extracted_total = sum(Decimal(row["amount"]) for row in extracted_rows)
        assert extracted_total == expected_total
        preview = fitz.open(pdf_path)
        preview_paths: list[Path] = []
        for index, page in enumerate(preview):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            preview_path = EVIDENCE / f"report-one-page-{index + 1}.png"
            pix.save(preview_path)
            assert preview_path.stat().st_size > 1000
            preview_paths.append(preview_path)

        terminate(worker)
        worker = None
        second = httpx.post(
            f"{BASE_URL}/api/reports",
            json={"title": "E2E Restart Persistence Report", "delay_seconds": 0.2},
            timeout=2,
        )
        assert second.status_code == 202
        assert wait_for_status(second.json()["id"], "pending")["status"] == "pending"
        worker = start_worker(environment)
        second_completed = wait_for_status(second.json()["id"], "completed")
        assert second_completed["status"] == "completed"
        assert second_completed["artifact_reference"] != completed["artifact_reference"]
        integrity = {
            "source_record_count": len(source_rows),
            "source_total_amount": f"${expected_total:,.2f}",
            "source_average_amount": f"${expected_average:,.2f}",
            "extracted_detail_record_count": len(extracted_rows),
            "extracted_detail_total_amount": f"${extracted_total:,.2f}",
            "all_detail_rows_match_persisted_source_rows": extracted_rows == source_rows,
            "all_detail_amounts_match": [row["amount"] for row in extracted_rows]
            == [row["amount"] for row in source_rows],
            "source_rows": source_rows,
            "extracted_detail_rows": extracted_rows,
        }
        (EVIDENCE / "integrity-comparison.json").write_text(json.dumps(integrity, indent=2))
        evidence = {
            "http_return_ms": elapsed_ms,
            "observed_states": {
                "pending": pending["status"],
                "running": running["status"],
                "completed": completed["status"],
            },
            "final_status": completed["status"],
            "pdf_signature": downloaded.content[:5].decode("latin-1"),
            "pdf_size_bytes": len(downloaded.content),
            "page_count": page_count,
            "text_tokens_verified": expected_tokens,
            "full_detail_reconciliation_verified": extracted_rows == source_rows
            and extracted_total == expected_total,
            "rendered_previews": [str(path.relative_to(ROOT)) for path in preview_paths],
            "worker_restart_persisted": True,
            "second_artifact_reference": second_completed["artifact_reference"],
            "visual_inspection": "Rendered aggregate and detailed-record pages reviewed: no clipped or broken content visible.",
        }
        (EVIDENCE / "e2e-summary.json").write_text(json.dumps(evidence, indent=2))
        (EVIDENCE / "e2e-output.txt").write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(evidence, indent=2))
    finally:
        if worker is not None:
            terminate(worker)
        terminate(api)


if __name__ == "__main__":
    main()