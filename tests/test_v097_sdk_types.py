"""TDD coverage for schema-aware TypeScript SDK generation."""
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


def test_sdk_emits_openapi_component_interfaces_and_typed_request_body(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["sdk", "generate", "--project", str(project)])
    assert result.exit_code == 0, result.output
    client = (project / "sdk/typescript/client.ts").read_text()
    assert "export interface ItemCreate" in client
    assert "name: string;" in client
    assert "async createItem(body: ItemCreate" in client


def test_schema_renderer_handles_arrays_nullable_and_optional_fields(tmp_path: Path) -> None:
    project = _project(tmp_path)
    main = project / "app/main.py"
    main.write_text(main.read_text() + '''
from pydantic import BaseModel
class Profile(BaseModel):
    tags: list[str]
    nickname: str | None = None
@app.post('/profiles', response_model=Profile)
async def create_profile(profile: Profile) -> Profile:
    return profile
''')
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project)]).exit_code == 0
    client = (project / "sdk/typescript/client.ts").read_text()
    assert "tags: string[];" in client
    assert "nickname?: null | string;" in client or "nickname?: string | null;" in client
    assert "Promise<Profile>" in client


def test_sdk_output_is_byte_stable_for_unchanged_contract(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project)]).exit_code == 0
    before = (project / "sdk/typescript/client.ts").read_bytes()
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project)]).exit_code == 0
    assert (project / "sdk/typescript/client.ts").read_bytes() == before


def test_lock_records_client_sha256(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert runner.invoke(app, ["sdk", "generate", "--project", str(project)]).exit_code == 0
    lock = json.loads((project / "sdk/typescript/openapi-lock.json").read_text())
    assert len(lock["client_sha256"]) == 64
