# Requirements audit

| Preserved core contract | Evidence |
| --- | --- |
| On-demand request returns promptly | `POST /api/reports` creates a `pending` job and returns HTTP 202; E2E captures request timing before completion. |
| Work runs outside HTTP request | `report_service.worker` is a separate process that claims pending jobs. |
| Persisted source data and real aggregation | SQLite `source_records` is seeded; the worker queries it and computes counts, totals, averages, and category totals. |
| Useful readable PDF | ReportLab renders an aggregate and detailed record listing; `pypdf` validates it before atomic publish. |
| Unique retained artifacts and status | UUID job IDs generate separate PDF names and persist terminal state in SQLite. |
| Predictable failure handling | `simulate_failure` drives the worker into `failed`; it exposes no artifact. |
| Partial-output safety | PDFs render to a `.partial` file, validate, then atomically rename before `completed` is stored. |
| Data-to-PDF integrity | Tests and E2E compare persisted-source aggregate tokens against extracted PDF text. |
| Scheduling | Deliberately omitted as stretch work. |

## Assumption boundary

This audit checks the supplied core contract only. The unavailable original brief leaves the endpoint names, request shape, storage, data model, report composition, and implementation technology as local choices rather than claimed FlyRank requirements.