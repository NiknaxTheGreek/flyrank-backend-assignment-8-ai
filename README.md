# FlyRank Backend Assignment 8 — PDF Report Generator

A FastAPI + separate-worker implementation of the recovered Assignment 8 portal contract:

```text
query data → aggregate/prepare data → background job → render PDF → store artifact → expose artifact reference/result
```

The assignment's authoritative S3 source intentionally does **not** prescribe exact routes, libraries, database schema, queue technology, or PDF layout. This implementation uses SQLite, a polling worker, ReportLab, `pypdf`, PyMuPDF, and filesystem artifact storage as small local engineering choices.

## S3 behaviour

`POST /api/reports` creates a persisted report job and returns HTTP `202` while it is still `pending`. A separate `python -m report_service.worker` process claims pending jobs, queries the persisted source rows, prepares aggregate values, renders the report to a temporary file, validates the PDF, atomically publishes it, and stores only the resulting filename/reference in the job row.

The PDF binary is **not** carried inside the job payload or job record. The database stores `artifact_reference`, and `GET /api/reports/{job_id}/result` resolves that reference to the stored PDF when the job is complete. This directly implements S3's “store and link; do not pass a large artifact through job payloads” rule.

## Routes

These route names are implementation choices, not FlyRank-mandated names:

| Route | Purpose |
| --- | --- |
| `GET /api/healthz` | health check |
| `POST /api/reports` | create on-demand report job; returns `202` |
| `GET /api/reports/{job_id}` | inspect job status and artifact reference |
| `GET /api/reports/{job_id}/result` | retrieve the completed PDF |
| `GET /api/reports` | list retained report jobs |
| `GET /api/source-summary` | expose the aggregate used for integrity checking |

## Install and run

Python 3.12+ is required. From the repository root:

```bash
python -m pip install .
```

Start the API:

```bash
cd artifacts/flyrank-pdf-report-generator
python -m uvicorn report_service.api:app --port 8000
```

Start the worker in a second terminal from the same directory:

```bash
python -m report_service.worker
```

Example on-demand request:

```bash
curl -i -X POST http://127.0.0.1:8000/api/reports \
  -H 'content-type: application/json' \
  -d '{"title":"Monthly Source Performance Report"}'
```

Poll the returned job ID with `GET /api/reports/{job_id}`. Once `status` is `completed`, `artifact_reference` identifies the stored file and `/result` returns the PDF.

## Current verification

GitHub Actions run **32711411586** executed the current report pipeline on 2026-08-24 after the recovered S3 audit:

- Python compilation: PASS;
- **8 automated tests passed**;
- initial HTTP report request returned in **22.2 ms** before worker completion;
- observed states: `pending → running → completed`;
- generated PDF signature: `%PDF-`;
- generated PDF size: **3,659 bytes**;
- PDF pages: **2**;
- persisted source records: **12**;
- report total: **$19,657.00**;
- report average: **$1,638.08**;
- every extracted detail row/order/amount reconciled exactly to SQLite source data;
- the worker was terminated/restarted and a second job produced a distinct retained PDF reference;
- CI printed `A8_BACKGROUND_PDF_GATE=PASS` and uploaded the generated runtime evidence.

The E2E script also renders both PDF pages to PNG and asserts that render files are non-empty. An older evidence record contains a visual-review statement; the current GitHub Actions gate itself is treated as automated render evidence, not as a new human visual inspection.

## Failure safety

`simulate_failure: true` is a test-oriented implementation switch that exercises controlled worker failure. Failed jobs expose no artifact reference. PDF generation writes to a `.partial` path first, validates the completed document, then atomically renames it before the job is marked completed, reducing the risk of exposing a partially written report.

## Verification commands

```bash
PYTHONPATH=artifacts/flyrank-pdf-report-generator \
python -m pytest artifacts/flyrank-pdf-report-generator/report_service/tests -q

python artifacts/flyrank-pdf-report-generator/report_service/scripts/e2e_verify.py
```

See [`REQUIREMENTS_AUDIT.md`](REQUIREMENTS_AUDIT.md) for the recovered-S3 mapping and [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md) for the current checkpoint summary.

## Stretch boundary

Scheduling report generation is an individual optional stretch item in S3 and is intentionally not implemented. It is not required for Assignment 8 core completion.

Assignments 8 and 9 currently have no separate explicit S4 prompt/rematch exercise in the recovered S3 source.
