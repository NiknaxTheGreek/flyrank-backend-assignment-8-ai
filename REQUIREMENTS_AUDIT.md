# Requirements audit

| Preserved core contract | Evidence |
| --- | --- |
| On-demand request returns promptly | `POST /api/reports` creates a `pending` job and returns HTTP 202; the latest E2E checkpoint returned in 15.1 ms before worker completion. |
| Work runs outside HTTP request | `report_service.worker` is a separate process that claims pending jobs. The E2E checkpoint starts it only after recording `pending`, then records `running` and `completed`. |
| Persisted source data and real aggregation | SQLite `source_records` is seeded; the worker queries it and computes counts, totals, averages, and category totals. |
| Useful readable PDF | ReportLab renders an aggregate and detailed record listing; `pypdf` validates it before atomic publish. |
| Unique retained artifacts and status | UUID job IDs generate separate PDF names and persist terminal state in SQLite. The latest E2E run retained two distinct PDF artifacts across worker restart. |
| Predictable failure handling | `simulate_failure` drives the worker into `failed`; it exposes no artifact. A dedicated completed-job/missing-artifact test verifies the result endpoint returns documented HTTP 404 rather than a PDF. |
| Partial-output safety | PDFs render to a `.partial` file, validate, then atomically rename before `completed` is stored. |
| Data-to-PDF integrity | The latest E2E run queries persisted source rows, recomputes count, total, and average, extracts every detailed PDF row and amount, and verifies exact row/order/amount equality plus total reconciliation. |
| Scheduling | Deliberately omitted as stretch work. |

## Assumption boundary

This audit checks the supplied core contract only. The unavailable original brief leaves the endpoint names, request shape, storage, data model, report composition, and implementation technology as local choices rather than claimed FlyRank requirements.