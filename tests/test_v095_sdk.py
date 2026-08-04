"""TDD acceptance coverage for the OpenAPI to TypeScript SDK lifecycle."""
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


def test_sdk_generate_creates_deterministic_typed_client(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["sdk", "generate", "--project", str(project), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    client = (project / "sdk/typescript/client.ts").read_text()
    metadata = json.loads((project / "sdk/typescript/openapi-lock.json").read_text())
    assert payload["status"] == "generated"
    assert "export class ApiClient" in client
    assert "async getHealth" in client
    assert "async createItem" in client
    assert "Promise<unknown>" in client
    assert metadata["openapi_sha256"] == payload["openapi_sha256"]
    assert "generated_at" not in metadata


def test_sdk_check_detects_fresh_and_stale_contracts(tmp_path: Path) -> None:
    project = _project(tmp_path)
    generated = runner.invoke(app, ["sdk", "generate", "--project", str(project), "--json"])
    assert generated.exit_code == 0, generated.output
    fresh = runner.invoke(app, ["sdk", "check", "--project", str(project), "--json"])
    assert fresh.exit_code == 0, fresh.output
    assert json.loads(fresh.stdout)["status"] == "fresh"

    main = project / "app/main.py"
    main.write_text(main.read_text() + "\n@app.get('/new-route')\nasync def new_route():\n    return {'ok': True}\n")
    stale = runner.invoke(app, ["sdk", "check", "--project", str(project), "--json"])
    assert stale.exit_code == 1
    assert json.loads(stale.stdout)["status"] == "stale"


def test_sdk_dry_run_writes_nothing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["sdk", "generate", "--project", str(project), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["status"] == "preview"
    assert not (project / "sdk").exists()


def test_sdk_rejects_application_import_failure_without_leaking_exception(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "app/main.py").write_text("raise RuntimeError('private detail')\n")
    result = runner.invoke(app, ["sdk", "generate", "--project", str(project), "--json"])
    assert result.exit_code == 1
    assert "private detail" not in result.stdout
    assert "Traceback" not in result.stdout
