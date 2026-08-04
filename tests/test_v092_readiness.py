"""TDD acceptance coverage for evidence-based readiness diagnostics."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit.cli import app

runner = CliRunner()


def _project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    project = tmp_path / "demo"
    (project / ".env").write_text(
        "DATABASE_URL=sqlite+aiosqlite:///./ready.db\n"
        "AUTH_JWT_SECRET_KEY=" + "x" * 48 + "\n",
        encoding="utf-8",
    )
    return project


def _checks(result: object) -> dict[str, dict[str, object]]:
    payload = json.loads(result.stdout)  # type: ignore[attr-defined]
    return {check["name"]: check for check in payload["checks"]}


def test_doctor_connectivity_checks_real_sqlite_and_app_import(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["doctor", "--project", str(project), "--environment",
                                 "production", "--connectivity", "--startup", "--json"])
    assert result.exit_code == 0, result.output
    checks = _checks(result)
    assert checks["database-connectivity"]["ok"] is True
    assert checks["application-import"]["ok"] is True
    assert checks["database-connectivity"]["duration_ms"] >= 0
    assert "sqlite" in str(checks["database-connectivity"]["detail"]).lower()


def test_doctor_connectivity_reports_actionable_database_failure(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / ".env").write_text(
        "DATABASE_URL=unsupported://broken\nAUTH_JWT_SECRET_KEY=" + "x" * 48 + "\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["doctor", "--project", str(project), "--connectivity", "--json"])
    assert result.exit_code == 1
    check = _checks(result)["database-connectivity"]
    assert check["ok"] is False
    assert check["code"] == "database_url_unsupported"
    assert "sqlite" in str(check["remediation"]).lower()


def test_doctor_startup_reports_import_error_without_traceback(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "app/main.py").write_text("raise RuntimeError('secret internal failure')\n", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--project", str(project), "--startup", "--json"])
    assert result.exit_code == 1
    check = _checks(result)["application-import"]
    assert check["ok"] is False
    assert check["code"] == "application_import_failed"
    assert "secret internal failure" not in result.stdout
    assert "Traceback" not in result.stdout


def test_doctor_connection_checks_are_opt_in(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["doctor", "--project", str(project), "--json"])
    checks = _checks(result)
    assert "database-connectivity" not in checks
    assert "application-import" not in checks
