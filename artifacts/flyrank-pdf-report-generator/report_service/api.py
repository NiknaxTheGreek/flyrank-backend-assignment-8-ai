from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .database import artifact_path, create_job, fetch_source_records, get_job, initialize_database, list_jobs, source_summary


class ReportRequest(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    delay_seconds: float = Field(default=0.4, ge=0, le=10)
    simulate_failure: bool = False


class ReportJob(BaseModel):
    id: str
    title: str
    status: Literal["pending", "running", "completed", "failed"]
    created_at: str
    updated_at: str
    started_at: str | None
    completed_at: str | None
    artifact_reference: str | None
    error_message: str | None
    source_record_count: int


class SourceSummary(BaseModel):
    record_count: int
    total_amount: float
    average_amount: float
    category_totals: dict[str, float]


app = FastAPI(
    title="Independent PDF Report Generator",
    description=(
        "Implementation-assumption API. It is not presented as a recovered FlyRank route contract."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/api/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reports", response_model=ReportJob, status_code=202)
def queue_report(request: ReportRequest) -> ReportJob:
    return ReportJob.model_validate(create_job(**request.model_dump()))


@app.get("/api/reports", response_model=list[ReportJob])
def reports() -> list[ReportJob]:
    return [ReportJob.model_validate(job) for job in list_jobs()]


@app.get("/api/reports/{job_id}", response_model=ReportJob)
def report_status(job_id: str) -> ReportJob:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Report job not found")
    return ReportJob.model_validate(job)


@app.get("/api/reports/{job_id}/result")
def report_result(job_id: str) -> Response:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Report job not found")
    if job["status"] != "completed" or not job["artifact_reference"]:
        raise HTTPException(status_code=409, detail="Report is not completed")
    try:
        path = artifact_path(str(job["artifact_reference"]))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Report artifact not found") from error
    if not path.is_file() or path.stat().st_size < 100:
        raise HTTPException(status_code=404, detail="Report artifact not found")
    return FileResponse(path, media_type="application/pdf", filename=f"report-{job_id}.pdf")


@app.get("/api/source-summary", response_model=SourceSummary)
def source_data_summary() -> SourceSummary:
    return SourceSummary.model_validate(source_summary(fetch_source_records()))