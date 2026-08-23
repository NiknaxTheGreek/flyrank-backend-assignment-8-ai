# Source gap and implementation assumptions

The original S3/FlyRank Assignment 8 brief was unavailable at implementation time. No claim is made that any of the following are FlyRank-mandated:

- API route names, request fields, response schema, or status codes;
- the FastAPI, SQLite, ReportLab, `pypdf`, and PyMuPDF stack;
- a polling worker as the job-queue mechanism;
- filesystem artifact storage or UUID filenames;
- seeded invoice-like source records;
- aggregate and detailed-record PDF layout;
- a controlled `simulate_failure` test switch.

These choices preserve the explicit core contract using the smallest maintainable implementation appropriate to this environment. Scheduling remains intentionally unimplemented stretch work. The S4 human-vs-AI rematch comparison remains pending until a separate human implementation exists.