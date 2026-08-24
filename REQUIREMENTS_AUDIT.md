# Assignment 8 Requirements Audit

Authoritative source: recovered S3 — **Assignment 8: PDF Report Generator**. S3 records that no PDF was supplied and the available portal description is authoritative. It explicitly avoids inventing unspecified routes, libraries, schemas, queue technology, database design, or PDF format.

| S3 requirement | Current implementation / evidence | Status |
| --- | --- | --- |
| Query report data | worker reads persisted SQLite `source_records`; E2E independently queries the same source rows for reconciliation | PASS |
| Prepare / aggregate data | `source_summary()` computes record count, total, average and category totals | PASS |
| Render a PDF | ReportLab renders aggregate and detailed source rows; `pypdf` validates the published document | PASS |
| Generate as background work | HTTP request persists a `pending` job; a separate worker process claims it and performs generation | PASS |
| Initial generation is on-demand | `POST /api/reports` creates report jobs on demand | PASS |
| Store generated artifact | completed PDFs are retained in the configured report output directory | PASS |
| Expose/reference the artifact | job row stores only `artifact_reference`; status API exposes it and `/result` resolves it to the stored PDF | PASS |
| Do not carry large PDF through job payload | report job contains metadata/reference only; PDF bytes are filesystem artifact data, not queue/database job payload | PASS |
| Current async behaviour evidence | run `32711411586` observed `pending → running → completed`; request returned in 22.2 ms before worker processing completed | PASS |
| Current PDF validity evidence | `%PDF-` signature, 3,659 bytes, 2 pages | PASS |
| Current data integrity evidence | 12 persisted rows; every extracted detail row/order/amount matched SQLite; totals $19,657.00 and average $1,638.08 matched | PASS |
| Independent retained artifact evidence | worker restart followed by second completed job with a distinct PDF reference | PASS |
| Automated tests | run `32711411586`: 8 tests passed | PASS |
| Clean install | root `pyproject.toml` explicitly scopes setuptools package discovery to `report_service`; final CI proves `python -m pip install .` | PENDING FINAL CI AFTER PACKAGING COMMIT |
| Scheduling | S3 identifies scheduling as optional stretch; intentionally omitted | OPTIONAL — NOT REQUIRED |
| S4 prompt/rematch stage | recovered S3 lists no separate Assignment 8 S4 prompt exercise | NOT REQUIRED BY CURRENT SOURCE |

## Implementation choices, not FlyRank requirements

The current API paths, FastAPI, SQLite, ReportLab, `pypdf`, PyMuPDF, polling worker, filesystem storage, UUID filenames, seeded invoice-like rows, PDF layout, and `simulate_failure` switch are local implementation decisions. They satisfy the portal-level architecture without being presented as mandated technology.

## Failure and artifact safety

The implementation additionally provides controlled failed jobs and partial-output protection. PDFs render to a `.partial` path, are validated, and are atomically renamed before completion is persisted. These are useful engineering safeguards but are not being promoted into invented S3 requirements.

## Completion boundary

Assignment 8 core behaviour is proven by current runtime evidence. Scheduling remains an optional stretch. Final repository acceptance waits only for the clean-install/documentation CI rerun after the packaging and recovered-S3 documentation updates.
