"""TDD coverage for deterministic schema-aware Python SDK generation."""
from __future__ import annotations

import hashlib
import json
import py_compile
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit.cli import app

runner = CliRunner()


def _project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    return tmp_path / "demo"


def test_python_sdk_generates_typed_models_and_client(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["sdk", "generate", "--project", str(project),
                                 "--language", "python", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    client_path = project / "sdk/python/client.py"
    client = client_path.read_text()
    assert payload["language"] == "python"
    assert "class ItemCreate(TypedDict):" in client
    assert "name: str" in client
    assert "def create_item(" in client
    assert "body: ItemCreate" in client
    assert "class ApiError(RuntimeError):" in client
    py_compile.compile(str(client_path), doraise=True)


def test_python_sdk_uses_standard_library_only_and_encodes_path_params(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project),
                               "--language", "python"]).exit_code == 0
    client = (project / "sdk/python/client.py").read_text()
    assert "from urllib.request import Request, urlopen" in client
    assert "from urllib.parse import quote" in client
    assert "requests" not in client
    assert "httpx" not in client
    assert "quote(str(item_id), safe='')" in client


def test_python_sdk_check_detects_tampered_client(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project),
                               "--language", "python"]).exit_code == 0
    fresh = runner.invoke(app, ["sdk", "check", "--project", str(project),
                                "--language", "python", "--json"])
    assert fresh.exit_code == 0, fresh.output
    path = project / "sdk/python/client.py"
    path.write_text(path.read_text() + "\n# manual drift\n")
    stale = runner.invoke(app, ["sdk", "check", "--project", str(project),
                                "--language", "python", "--json"])
    assert stale.exit_code == 1
    assert json.loads(stale.stdout)["status"] == "stale"


def test_python_sdk_is_deterministic_and_records_client_hash(tmp_path: Path) -> None:
    project = _project(tmp_path)
    args = ["sdk", "generate", "--project", str(project), "--language", "python"]
    assert runner.invoke(app, args).exit_code == 0
    client_path = project / "sdk/python/client.py"
    before = client_path.read_bytes()
    assert runner.invoke(app, args).exit_code == 0
    assert client_path.read_bytes() == before
    lock = json.loads((project / "sdk/python/openapi-lock.json").read_text())
    assert lock["client_sha256"] == hashlib.sha256(before).hexdigest()
