# Assignment 8 Source Status and Implementation Choices

The authoritative S3 source has now been recovered. It records that **no separate Assignment 8 PDF was supplied** and that the available FlyRank portal description is the authoritative source currently available.

The recovered S3 core contract is:

```text
query data → aggregate/prepare data → render PDF → background job → store/link result
```

It also explicitly warns against inventing unspecified routes, libraries, schemas, job payloads, PDF format, queue technology, or database design. Therefore the following remain implementation choices rather than FlyRank-mandated technologies:

- API route names, request fields, response schema, and status details beyond the portal-level behaviour;
- FastAPI;
- SQLite;
- ReportLab, `pypdf`, and PyMuPDF;
- the polling worker as the local background-job mechanism;
- filesystem artifact storage and UUID PDF filenames;
- seeded invoice-like source records;
- aggregate + detailed-record report layout;
- the `simulate_failure` verification switch.

These choices are retained because the current implementation has real passing evidence for the required architecture and replacing them would add complexity without satisfying an additional source requirement.

Scheduling is explicitly an individual optional stretch item and remains intentionally unimplemented.

Recovered S3 also states that Assignments 8 and 9 currently contain no separate explicit S4 prompt exercise.
