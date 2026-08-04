"""TDD acceptance coverage for SDK freshness in deployment readiness."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit.cli import app

runner = CliRunner()


def _project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    return tmp_path / "demo"


def _sdk_check(result: object) -> dict[str, object]:
    payload = json.loads(result.stdout)  # type: ignore[attr-defined]
    return next(check for check in payload["checks"] if check["name"] == "sdk-freshness")


def test_doctor_sdk_reports_fresh_generated_client(tmp_path: Path) -> None:
    project = _project(tmp_path)
    generated = runner.invoke(app, ["sdk", "generate", "--project", str(project)])
    assert generated.exit_code == 0, generated.output
    result = runner.invoke(app, ["doctor", "--project", str(project), "--sdk", "--json"])
    assert result.exit_code == 0, result.output
    check = _sdk_check(result)
    assert check["ok"] is True
    assert check["code"] == "sdk_fresh"
    assert check["blocking"] is True


def test_doctor_sdk_blocks_stale_client_after_route_change(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project)]).exit_code == 0
    main = project / "app/main.py"
    main.write_text(main.read_text() + "\n@app.get('/added')\nasync def added():\n    return {'ok': True}\n")
    result = runner.invoke(app, ["doctor", "--project", str(project), "--sdk", "--json"])
    assert result.exit_code == 1
    check = _sdk_check(result)
    assert check["ok"] is False
    assert check["code"] == "sdk_stale"
    assert "sdk generate" in str(check["remediation"])


def test_doctor_sdk_reports_missing_lock_without_exception_details(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["doctor", "--project", str(project), "--sdk", "--json"])
    assert result.exit_code == 1
    check = _sdk_check(result)
    assert check["code"] == "sdk_missing"
    assert "Traceback" not in result.stdout


def test_doctor_sdk_is_opt_in(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["doctor", "--project", str(project), "--json"])
    assert result.exit_code == 0
    names = {check["name"] for check in json.loads(result.stdout)["checks"]}
    assert "sdk-freshness" not in names
