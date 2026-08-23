# PDF Report Generator

An independent implementation of a PDF report-generation assignment. It accepts report jobs over HTTP, processes them in a separate worker, aggregates persisted SQLite source records, renders validated PDFs, and retains independent artifacts.

## Important source boundary

The original S3/FlyRank brief is unavailable. This repository does **not** claim that its routes, schemas, SQLite database, FastAPI/ReportLab libraries, filesystem storage, worker polling mechanism, or report layout were mandated by FlyRank. They are small, maintainable implementation assumptions selected for this project.

## Run locally

```bash
cd artifacts/flyrank-pdf-report-generator
python -m uvicorn report_service.api:app --port 8000
# In a second terminal from the same directory:
python -m report_service.worker
```

The FastAPI service exposes implementation-assumption routes:

- `POST /api/reports` accepts a request and returns a `pending` job with HTTP 202.
- `GET /api/reports/{job_id}` returns observable status.
- `GET /api/reports/{job_id}/result` returns a completed PDF only.
- `GET /api/reports` retains and lists independent report jobs.
- `GET /api/source-summary` exposes the aggregate used for integrity checks.

Use `simulate_failure: true` in a creation request to exercise controlled failure behavior. Scheduling is intentionally omitted: it is stretch work, not a prerequisite of the core contract.

## Verification

```bash
PYTHONPATH=artifacts/flyrank-pdf-report-generator pytest artifacts/flyrank-pdf-report-generator/report_service/tests -q
python artifacts/flyrank-pdf-report-generator/report_service/scripts/e2e_verify.py
```

The latest recorded checkpoint completed on the local verification runtime with:

- 8 automated tests passing (3 dependency deprecation warnings);
- a report request returning in 15.1 ms before worker completion;
- observed `pending`, `running`, and `completed` states;
- a valid 3,660-byte, two-page PDF;
- full row-by-row reconciliation of all persisted source records and amounts against extracted PDF detail rows;
- a separate-worker restart that produced a distinct retained artifact.

The end-to-end verification writes PDFs, two PNG page renders, logs, and the complete data-to-PDF comparison under `verification_evidence/`.