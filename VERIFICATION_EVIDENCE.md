# Verification evidence

Run the commands below to refresh the durable runtime evidence:

```bash
PYTHONPATH=artifacts/flyrank-pdf-report-generator pytest artifacts/flyrank-pdf-report-generator/report_service/tests -q | tee verification_evidence/pytest-output.txt
python artifacts/flyrank-pdf-report-generator/report_service/scripts/e2e_verify.py
```

The E2E run produces:

- `report-one.pdf` — downloaded HTTP result;
- `report-one-page-1.png` and `report-one-page-2.png` — rendered previews of the aggregate and detailed-record PDF pages;
- `e2e-summary.json` and `e2e-output.txt` — request timing, explicitly observed `pending`/`running`/`completed` states, signature, size, page count, restart persistence, and visual review;
- `integrity-comparison.json` — persisted source rows, fully extracted detailed PDF rows, per-row amounts, and aggregate reconciliation;
- `runtime/` — SQLite data and generated worker artifacts proving persistence.

The implementation’s safety condition is that only a fully rendered, readable PDF is atomically published and then marked `completed`. A failure leaves the job `failed` and removes partial output.

## Latest observed checkpoint

- Automated suite: **8 passed, 3 warnings in 0.93s**.
- E2E request return time: **15.1 ms**.
- States captured in order: **pending → running → completed**.
- Downloaded PDF: **`%PDF-` signature, 3,660 bytes, 2 pages**.
- Integrity: **all 12 extracted detailed rows and amounts exactly matched the persisted source rows; recomputed total was $19,657.00 and average was $1,638.08**.
- Worker restart: a second completed report retained a distinct artifact reference.
- Render review: aggregate and detailed-record PNG pages showed no clipped or broken content.