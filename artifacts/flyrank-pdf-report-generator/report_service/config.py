from __future__ import annotations

import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent
DEFAULT_RUNTIME_DIR = SERVICE_DIR / "runtime"
DEFAULT_REPORTS_DIR = SERVICE_DIR / "reports"


def database_path() -> Path:
    return Path(os.environ.get("REPORT_DB_PATH", DEFAULT_RUNTIME_DIR / "reports.sqlite3"))


def reports_dir() -> Path:
    return Path(os.environ.get("REPORT_OUTPUT_DIR", DEFAULT_REPORTS_DIR))