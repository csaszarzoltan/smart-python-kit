"""Read-only, evidence-based generated-project readiness checks."""
from __future__ import annotations

import logging
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

Check = dict[str, Any]

logger = logging.getLogger("smartvintaawesomekit.readiness")


def _log_check(result: Check) -> None:
    """Emit a structured log record for one readiness check."""
    logger.info(
        "readiness check completed",
        extra={
            "check": result["name"],
            "ok": result["ok"],
            "code": result.get("code"),
            "duration_ms": result.get("duration_ms"),
        },
    )


def _environment(project: Path) -> dict[str, str]:
    """Read simple environment assignments without exposing their values."""
    values = dict(os.environ)
    for filename in (".env.example", ".env"):
        path = project / filename
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _check_database(project: Path) -> Check:
    """Perform a bounded, non-destructive database connectivity probe."""
    started = time.perf_counter()
    url = _environment(project).get("DATABASE_URL", "")
    base: Check = {"name": "database-connectivity", "blocking": True}
    if not url:
        return {**base, "ok": False, "code": "database_url_missing", "detail": "DATABASE_URL is not configured",
                "remediation": "Set DATABASE_URL in .env", "duration_ms": 0}
    if url.startswith(("sqlite://", "sqlite+aiosqlite://")):
        raw_path = url.split("///", 1)[1] if "///" in url else ":memory:"
        database = ":memory:" if raw_path == ":memory:" else str((project / raw_path).resolve())
        try:
            connection = sqlite3.connect(database, timeout=2)
            connection.execute("SELECT 1").fetchone()
            connection.close()
        except sqlite3.Error:
            return {**base, "ok": False, "code": "database_unreachable", "detail": "SQLite probe failed",
                    "remediation": "Check DATABASE_URL and directory permissions",
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2)}
        return {**base, "ok": True, "code": "database_ready", "detail": "SQLite connection and SELECT 1 succeeded",
                "remediation": "none", "duration_ms": round((time.perf_counter() - started) * 1000, 2)}
    scheme = urlparse(url).scheme
    return {**base, "ok": False, "code": "database_url_unsupported",
            "detail": f"Connectivity probe does not support scheme '{scheme}'",
            "remediation": "Use SQLite for local verification or install and run the PostgreSQL readiness integration",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2)}


def check_database(project: Path) -> Check:
    """Perform a bounded, non-destructive database connectivity probe.

    Emits a structured ``database-connectivity`` log record describing the
    outcome. Returns the check result dict.
    """
    result = _check_database(project)
    _log_check(result)
    return result


def _check_application_import(project: Path) -> Check:
    """Import the generated ASGI app in an isolated, time-bounded process."""
    started = time.perf_counter()
    command = [sys.executable, "-c", "from app.main import app; assert app is not None"]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, [str(project), os.environ.get("PYTHONPATH", "")]))
    try:
        result = subprocess.run(command, cwd=project, env=environment, capture_output=True,
                                text=True, timeout=10, check=False)
    except subprocess.TimeoutExpired:
        return {"name": "application-import", "ok": False, "blocking": True,
                "code": "application_import_timeout", "detail": "Application import exceeded 10 seconds",
                "remediation": "Remove blocking startup work from module import",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2)}
    ok = result.returncode == 0
    return {"name": "application-import", "ok": ok, "blocking": True,
            "code": "application_ready" if ok else "application_import_failed",
            "detail": "ASGI application imported successfully" if ok else "ASGI application import failed",
            "remediation": "none" if ok else "Run the app locally and inspect its startup logs",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2)}


def check_application_import(project: Path) -> Check:
    """Import the generated ASGI app in an isolated, time-bounded process.

    Emits a structured ``application-import`` log record describing the
    outcome. Returns the check result dict.
    """
    result = _check_application_import(project)
    _log_check(result)
    return result


__all__ = ["check_application_import", "check_database"]
