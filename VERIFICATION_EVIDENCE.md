# Verification evidence

Run the commands below to refresh the durable runtime evidence:

```bash
PYTHONPATH=artifacts/flyrank-pdf-report-generator pytest artifacts/flyrank-pdf-report-generator/report_service/tests -q | tee verification_evidence/pytest-output.txt
python artifacts/flyrank-pdf-report-generator/report_service/scripts/e2e_verify.py
```

The E2E run produces:

- `report-one.pdf` — downloaded HTTP result;
- `report-one-page-1.png` and `report-one-page-2.png` — rendered previews of the aggregate and detailed-record PDF pages;
- `e2e-summary.json` and `e2e-output.txt` — request timing, state, signature, size, page count, and visual review;
- `integrity-comparison.json` — expected source aggregate versus extracted PDF tokens;
- `runtime/` — SQLite data and generated worker artifacts proving persistence.

The implementation’s safety condition is that only a fully rendered, readable PDF is atomically published and then marked `completed`. A failure leaves the job `failed` and removes partial output.