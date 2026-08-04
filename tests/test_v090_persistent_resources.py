"""TDD acceptance tests for persistent resource generation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit.cli import app

runner = CliRunner()


def _project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    return tmp_path / "demo"


def test_persistent_resource_dry_run_lists_complete_vertical_slice(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["add-resource", "product", "--project", str(project),
                                 "--field", "name:str:required", "--field", "price:float:required",
                                 "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    files = set(json.loads(result.stdout)["files"])
    assert {"app/models/products.py", "app/schemas/products.py", "app/services/products.py",
            "app/routes/products.py", "migrations/versions/0001_create_products.py",
            "tests/test_products.py"} <= files


def test_persistent_resource_generates_typed_crud_and_migration(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["add-resource", "product", "--project", str(project),
                                 "--field", "name:str:required", "--field", "price:float:required",
                                 "--field", "active:bool:optional"])
    assert result.exit_code == 0, result.output
    model = (project / "app/models/products.py").read_text()
    schemas = (project / "app/schemas/products.py").read_text()
    service = (project / "app/services/products.py").read_text()
    route = (project / "app/routes/products.py").read_text()
    migration = (project / "migrations/versions/0001_create_products.py").read_text()
    assert "class Product(Base)" in model and "Mapped[float]" in model
    assert "class ProductCreate" in schemas and "class ProductUpdate" in schemas
    assert "class ProductService" in service and "async def delete" in service
    assert "@router.patch" in route and "@router.delete" in route and "AsyncSession" in route
    assert "op.create_table" in migration and "op.drop_table" in migration


def test_generated_resource_real_sqlite_crud_integration(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["add-resource", "product", "--project", str(project),
                                 "--field", "name:str:required", "--field", "price:float:required"])
    assert result.exit_code == 0, result.output
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(project) + __import__("os").pathsep + env.get("PYTHONPATH", "")
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    completed = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_products.py"],
                               cwd=project, env=env, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_resource_rejects_duplicate_fields_before_writing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["add-resource", "product", "--project", str(project),
                                 "--field", "name:str:required", "--field", "name:str:optional"])
    assert result.exit_code != 0
    assert not (project / "app/models/products.py").exists()


def test_migrate_dry_run_exposes_safe_alembic_command(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["migrate", "upgrade", "--project", str(project),
                                 "--revision", "head", "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["command"] == ["alembic", "upgrade", "head"]
    assert payload["executed"] is False


def test_migrate_rejects_unsafe_revision(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = runner.invoke(app, ["migrate", "upgrade", "--project", str(project),
                                 "--revision", "head;rm -rf /"])
    assert result.exit_code != 0
