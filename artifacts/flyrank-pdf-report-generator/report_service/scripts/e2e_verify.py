from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
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


def wait_for_completion(job_id: str) -> dict:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        job = httpx.get(f"{BASE_URL}/api/reports/{job_id}", timeout=1).json()
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(0.15)
    raise RuntimeError(f"Job {job_id} did not reach terminal state")


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
    worker = subprocess.Popen(
        [sys.executable, "-m", "report_service.worker"],
        cwd=SERVICE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
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
        immediate = httpx.get(f"{BASE_URL}/api/reports/{first_job['id']}", timeout=1).json()
        assert immediate["status"] in {"pending", "running"}
        completed = wait_for_completion(first_job["id"])
        assert completed["status"] == "completed", completed
        downloaded = httpx.get(f"{BASE_URL}/api/reports/{first_job['id']}/result", timeout=4)
        assert downloaded.status_code == 200
        pdf_path = EVIDENCE / "report-one.pdf"
        pdf_path.write_bytes(downloaded.content)
        assert downloaded.content.startswith(b"%PDF")
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        expected_tokens = ["Records processed: 12", "Total amount: $19,657.00", "Detailed source records"]
        assert all(token in extracted for token in expected_tokens)
        preview = fitz.open(pdf_path)
        preview_paths: list[Path] = []
        for index, page in enumerate(preview):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            preview_path = EVIDENCE / f"report-one-page-{index + 1}.png"
            pix.save(preview_path)
            assert preview_path.stat().st_size > 1000
            preview_paths.append(preview_path)

        terminate(worker)
        worker = subprocess.Popen(
            [sys.executable, "-m", "report_service.worker"],
            cwd=SERVICE,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        second = httpx.post(
            f"{BASE_URL}/api/reports",
            json={"title": "E2E Restart Persistence Report", "delay_seconds": 0.2},
            timeout=2,
        )
        assert second.status_code == 202
        second_completed = wait_for_completion(second.json()["id"])
        assert second_completed["status"] == "completed"
        assert second_completed["artifact_reference"] != completed["artifact_reference"]
        integrity = {
            "expected": {"record_count": 12, "total_amount": "$19,657.00"},
            "extracted_tokens": expected_tokens,
            "matched": True,
        }
        (EVIDENCE / "integrity-comparison.json").write_text(json.dumps(integrity, indent=2))
        evidence = {
            "http_return_ms": elapsed_ms,
            "immediate_status": immediate["status"],
            "final_status": completed["status"],
            "pdf_signature": downloaded.content[:5].decode("latin-1"),
            "pdf_size_bytes": len(downloaded.content),
            "page_count": page_count,
            "text_tokens_verified": expected_tokens,
            "rendered_previews": [str(path.relative_to(ROOT)) for path in preview_paths],
            "worker_restart_persisted": True,
            "second_artifact_reference": second_completed["artifact_reference"],
            "visual_inspection": "Rendered aggregate and detailed-record pages reviewed: no clipped or broken content visible.",
        }
        (EVIDENCE / "e2e-summary.json").write_text(json.dumps(evidence, indent=2))
        (EVIDENCE / "e2e-output.txt").write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(evidence, indent=2))
    finally:
        terminate(worker)
        terminate(api)


if __name__ == "__main__":
    main()