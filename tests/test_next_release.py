import json
from pathlib import Path

import pytest
from sqlalchemy import column, select
from typer.testing import CliRunner

from smartvintaawesomekit.api import paginate
from smartvintaawesomekit.cli import app

runner = CliRunner()


def test_paginate_applies_offset_and_limit():
    query, page, size = paginate(select(column("id")), page=3, size=10)
    sql = str(query)
    assert page == 3 and size == 10
    assert "LIMIT" in sql and "OFFSET" in sql


@pytest.mark.parametrize("page,size", [(0, 20), (1, 0), (1, 101)])
def test_paginate_rejects_unsafe_values(page, size):
    with pytest.raises(ValueError):
        paginate(select(column("id")), page=page, size=size)


def test_generated_project_contains_migration_and_request_id_support(tmp_path: Path):
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    project = tmp_path / "demo"
    assert (project / "alembic.ini").is_file()
    assert (project / "migrations/env.py").is_file()
    assert (project / "app/middleware.py").is_file()
    assert "X-Request-ID" in (project / "app/middleware.py").read_text()


def test_add_resource_previews_then_generates_vertical_slice(tmp_path: Path):
    runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    project = tmp_path / "demo"
    preview = runner.invoke(app, ["add-resource", "product", "--project", str(project), "--field", "name:str:required", "--dry-run", "--json"])
    assert preview.exit_code == 0, preview.output
    assert json.loads(preview.stdout)["dry_run"] is True
    assert not (project / "app/routes/products.py").exists()
    result = runner.invoke(app, ["add-resource", "product", "--project", str(project), "--field", "name:str:required", "--field", "price:float:required"])
    assert result.exit_code == 0, result.output
    assert (project / "app/routes/products.py").is_file()
    assert (project / "tests/test_products.py").is_file()
    assert "products_router" in (project / "app/main.py").read_text()


def test_add_resource_refuses_duplicate(tmp_path: Path):
    runner.invoke(app, ["init", "demo", "--directory", str(tmp_path)])
    project = tmp_path / "demo"
    args = ["add-resource", "product", "--project", str(project), "--field", "name:str:required"]
    assert runner.invoke(app, args).exit_code == 0
    assert runner.invoke(app, args).exit_code != 0


def test_doctor_production_flags_missing_env_and_returns_nonzero(tmp_path: Path):
    runner.invoke(app, ["init", "demo", "--directory", str(tmp_path)])
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path / "demo"), "--environment", "production", "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["ok"] is False
    assert any(c["name"] == "production-env" and not c["ok"] for c in payload["checks"])
