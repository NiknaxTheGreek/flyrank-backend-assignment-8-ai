from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from .config import reports_dir
from .database import claim_next_job, complete_job, fail_job, fetch_source_records, initialize_database, source_summary
from .pdf_report import build_pdf, validate_pdf


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pdf-report-worker")


def process_one() -> bool:
    job = claim_next_job()
    if job is None:
        return False
    output_dir = reports_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    final_reference = f"{job['id']}.pdf"
    final_path = output_dir / final_reference
    partial_path = output_dir / f".{job['id']}.partial"
    try:
        delay = float(job["delay_seconds"])
        if delay:
            time.sleep(delay)
        if job["simulate_failure"]:
            partial_path.write_bytes(b"%PDF-1.4 deliberately incomplete test output")
            raise RuntimeError("Controlled worker failure requested for test coverage")
        records = fetch_source_records()
        summary = source_summary(records)
        build_pdf(partial_path, str(job["title"]), str(job["id"]), records, summary)
        validate_pdf(partial_path)
        os.replace(partial_path, final_path)
        complete_job(str(job["id"]), final_reference)
        logger.info("Completed report job %s with %s records", job["id"], len(records))
    except Exception as error:
        partial_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        fail_job(str(job["id"]), str(error))
        logger.exception("Report job %s failed", job["id"])
    return True


def main() -> None:
    initialize_database()
    poll_seconds = float(os.environ.get("REPORT_WORKER_POLL_SECONDS", "0.15"))
    logger.info("PDF report worker started")
    while True:
        if not process_one():
            time.sleep(poll_seconds)


if __name__ == "__main__":
    main()