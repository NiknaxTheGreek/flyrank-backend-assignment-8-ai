# Assignment 8 Verification Evidence

This file records executed observations. It does not infer successful runtime behaviour from code alone.

## Current GitHub Actions checkpoint — 2026-08-24

Run: `32711411586`

The current Assignment 8 implementation was executed on a GitHub-hosted Ubuntu runner with Python 3.13.

| Checkpoint | Observed result |
| --- | --- |
| Dependency installation | PASS |
| Python compilation | PASS |
| Automated tests | **8 passed**, 3 non-failing dependency/deprecation warnings |
| On-demand report request | HTTP `202`; returned in **22.2 ms** before worker completion |
| Background-state progression | `pending → running → completed` |
| Separate worker | E2E starts worker only after `pending` is observed |
| PDF signature | `%PDF-` |
| PDF size | **3,659 bytes** |
| PDF pages | **2** |
| Persisted source rows | **12** |
| Verified report total | **$19,657.00** |
| Verified report average | **$1,638.08** |
| Detailed reconciliation | every extracted PDF row/order/amount matched the SQLite source rows |
| Render evidence | two PNG page renders were generated and checked as non-empty files |
| Worker restart | first worker terminated; new worker processed second job successfully |
| Artifact retention | second completed report had a distinct `.pdf` artifact reference |
| Acceptance marker | `A8_BACKGROUND_PDF_GATE=PASS` |

The workflow uploaded the generated runtime directory as the `assignment-8-pdf-runtime-evidence` artifact.

## Important evidence boundary

The current CI run programmatically generated two page renders and verified their files. The E2E script also emits a pre-existing `visual_inspection` text field, but this automated CI run is **not** claimed as a new human visual inspection. The current acceptance claims only what the workflow actually executed and checked.

## Packaging follow-up

Run `32711411586` used explicit dependency installation after an earlier `pip install .` attempt exposed an unrelated flat-workspace setuptools discovery problem. The branch subsequently scopes root package discovery to `artifacts/flyrank-pdf-report-generator/report_service` and changes CI back to `python -m pip install .`. That clean-install checkpoint must pass before the branch is merged.

## Earlier evidence

The repository's earlier local E2E evidence independently recorded the same architectural behaviour: asynchronous request/worker separation, a valid two-page PDF, full source-data reconciliation, rendered pages, and a distinct artifact after worker restart. The current GitHub Actions run above supersedes that evidence for current-code runtime acceptance except for any explicitly manual visual-review claim.
