"""User-centered CLI for safe FastAPI project generation and diagnostics."""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from smartvintaawesomekit import __version__

app = typer.Typer(name="smartvintaawesomekit", help="Create and validate FastAPI projects.", no_args_is_help=True)
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
PRESETS = {"minimal", "api", "saas"}
DATABASES = {"sqlite", "postgresql"}

@dataclass(frozen=True)
class ProjectPlan:
    name: str
    destination: Path
    preset: str
    database: str


def _validate(name: str, preset: str, database: str) -> None:
    if not NAME.fullmatch(name):
        raise typer.BadParameter("Project name must start with a letter and contain only letters, numbers, '-' or '_'.")
    if preset not in PRESETS:
        raise typer.BadParameter(f"Unknown preset '{preset}'. Choose from: {', '.join(sorted(PRESETS))}.")
    if database not in DATABASES:
        raise typer.BadParameter(f"Unknown database '{database}'. Choose from: {', '.join(sorted(DATABASES))}.")


def _project_files(plan: ProjectPlan) -> dict[str, str]:
    postgres = plan.database == "postgresql"
    driver = '"asyncpg>=0.29.0"' if postgres else '"aiosqlite>=0.19.0"'
    db_url = "postgresql+asyncpg://app:app@localhost:5432/app" if postgres else "sqlite+aiosqlite:///./dev.db"
    files = {
        ".gitignore": ".env\n.venv/\n__pycache__/\n*.py[cod]\n.pytest_cache/\n.coverage\nhtmlcov/\n*.db\n",
        ".env.example": f"APP_NAME={plan.name}\nENVIRONMENT=development\nDATABASE_URL={db_url}\nLOG_LEVEL=INFO\n",
        ".smartvinta.json": json.dumps({"generator": "smartvintaawesomekit", "generator_version": __version__, "preset": plan.preset, "database": plan.database}, indent=2) + "\n",
        "app/__init__.py": "",
        "app/config.py": 'from pydantic_settings import BaseSettings, SettingsConfigDict\n\nclass Settings(BaseSettings):\n    app_name: str = "app"\n    environment: str = "development"\n    database_url: str = "sqlite+aiosqlite:///./dev.db"\n    log_level: str = "INFO"\n    model_config = SettingsConfigDict(env_file=".env", extra="ignore")\n\nsettings = Settings()\n',
        "app/database.py": 'from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine\nfrom app.config import settings\n\nengine = create_async_engine(settings.database_url, pool_pre_ping=True)\nsession_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)\n\nasync def get_db():\n    async with session_factory() as session:\n        yield session\n',
        "app/main.py": 'from fastapi import FastAPI\nfrom app.config import settings\n\napp = FastAPI(title=settings.app_name, version="0.1.0", description="Generated with SmartVintaAwesomeKit")\n\n@app.get("/", tags=["system"], summary="Service information")\nasync def root() -> dict[str, str]:\n    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}\n\n@app.get("/health", tags=["system"], summary="Health check")\nasync def health() -> dict[str, str]:\n    return {"status": "healthy", "version": "0.1.0"}\n',
        "tests/__init__.py": "",
        "tests/test_main.py": 'from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_health():\n    response = client.get("/health")\n    assert response.status_code == 200\n    assert response.json()["status"] == "healthy"\n\ndef test_root_guides_user_to_docs():\n    assert client.get("/").json()["docs"] == "/docs"\n',
        "pyproject.toml": f'[build-system]\nrequires = ["setuptools>=68", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "{plan.name}"\nversion = "0.1.0"\nrequires-python = ">=3.11"\ndependencies = ["fastapi>=0.136.0", "uvicorn[standard]>=0.20.0", "sqlalchemy>=2.0", {driver}, "pydantic-settings>=2.0"]\n\n[project.optional-dependencies]\ndev = ["pytest>=8,<9", "httpx>=0.24", "ruff>=0.3"]\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        "Dockerfile": 'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install --no-cache-dir .\nCMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n',
        "README.md": f'# {plan.name}\n\nGenerated with SmartVintaAwesomeKit {__version__}, preset **{plan.preset}**, database **{plan.database}**.\n\n## Quick start\n\n```bash\ncp .env.example .env\npython -m venv .venv\n. .venv/bin/activate\npip install -e ".[dev]"\npytest\nuvicorn app.main:app --reload\n```\n\nOpen <http://127.0.0.1:8000/docs>. Run `smartvintaawesomekit doctor --project .` before deployment. Never commit real secrets.\n',
    }
    files.update({
        "alembic.ini": "[alembic]\nscript_location = migrations\nprepend_sys_path = .\n",
        "migrations/env.py": "from alembic import context\nfrom app.database import engine\ntarget_metadata = None\n",
        "migrations/script.py.mako": "revision = ${repr(up_revision)}\ndown_revision = ${repr(down_revision)}\n\ndef upgrade():\n    pass\n\ndef downgrade():\n    pass\n",
        "migrations/versions/.gitkeep": "",
        "app/middleware.py": "from uuid import uuid4\nfrom starlette.middleware.base import BaseHTTPMiddleware\n\nclass RequestIDMiddleware(BaseHTTPMiddleware):\n    async def dispatch(self, request, call_next):\n        request_id = request.headers.get('X-Request-ID') or str(uuid4())\n        request.state.request_id = request_id\n        response = await call_next(request)\n        response.headers['X-Request-ID'] = request_id\n        return response\n",
    })
    if plan.preset in {"api", "saas"}:
        files["app/routes/__init__.py"] = ""
        files["app/routes/items.py"] = 'from fastapi import APIRouter, HTTPException\nfrom pydantic import BaseModel, Field\n\nrouter = APIRouter(prefix="/items", tags=["items"])\n_items: dict[int, dict] = {}\n\nclass ItemCreate(BaseModel):\n    name: str = Field(min_length=1, max_length=100)\n\n@router.post("", status_code=201)\nasync def create_item(item: ItemCreate) -> dict:\n    item_id = len(_items) + 1\n    value = {"id": item_id, "name": item.name}\n    _items[item_id] = value\n    return value\n\n@router.get("/{item_id}")\nasync def get_item(item_id: int) -> dict:\n    if item_id not in _items:\n        raise HTTPException(status_code=404, detail="Item not found")\n    return _items[item_id]\n'
        files["app/main.py"] = files["app/main.py"].replace("from app.config import settings", "from app.config import settings\nfrom app.routes.items import router as items_router").replace("\n@app.get(\"/\"", "\napp.include_router(items_router)\n\n@app.get(\"/\"")
        files["tests/test_items.py"] = 'from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_item_journey():\n    created = client.post("/items", json={"name": "First"})\n    assert created.status_code == 201\n    item_id = created.json()["id"]\n    assert client.get(f"/items/{item_id}").json()["name"] == "First"\n\ndef test_item_validation_is_visible():\n    assert client.post("/items", json={"name": ""}).status_code == 422\n'
    return files


def _write_atomic(plan: ProjectPlan, files: dict[str, str], force: bool) -> None:
    destination = plan.destination
    if destination.exists() and any(destination.iterdir()) and not force:
        raise typer.BadParameter(f"Destination '{destination}' is not empty. Use --force to replace generated files.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="smartvinta-") as temp:
        stage = Path(temp) / plan.name
        for relative, content in files.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        if destination.exists() and force:
            shutil.rmtree(destination)
        shutil.move(str(stage), str(destination))

@app.callback()
def callback() -> None:
    """Create projects and diagnose their local setup."""

@app.command()
def init(
    project_name: Annotated[str, typer.Argument(help="Project name")],
    directory: Annotated[str | None, typer.Option("--directory", "-d", help="Parent directory")] = None,
    database: Annotated[str, typer.Option(help="sqlite or postgresql")] = "sqlite",
    preset: Annotated[str, typer.Option(help="minimal, api, or saas")] = "api",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing")] = False,
    force: Annotated[bool, typer.Option("--force", help="Replace destination")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Machine-readable output")] = False,
) -> None:
    """Create a project safely, with a visible plan and clear next steps."""
    _validate(project_name, preset, database)
    base = Path(directory).expanduser().resolve() if directory else Path.cwd()
    plan = ProjectPlan(project_name, base / project_name, preset, database)
    files = _project_files(plan)
    payload = {"name": project_name, "destination": str(plan.destination), "preset": preset, "database": database}
    if dry_run:
        payload.update({"dry_run": True, "files": sorted(files)})
        typer.echo(json.dumps(payload, indent=2) if json_output else "Generation plan\n" + "\n".join(f"  create {p}" for p in sorted(files)))
        return
    _write_atomic(plan, files, force)
    next_steps = [f"cd {project_name}", "cp .env.example .env", "pip install -e '.[dev]'", "pytest", "uvicorn app.main:app --reload"]
    payload.update({"created_files": len(files), "next": next_steps})
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo(f"Created '{project_name}' at {plan.destination}")
        typer.echo(f"Preset: {preset}; database: {database}; files: {len(files)}")
        typer.echo("Next steps:\n  " + "\n  ".join(next_steps))
        typer.echo("Open http://127.0.0.1:8000/docs after starting the server.")

@app.command()
def doctor(project: Annotated[Path, typer.Option("--project")] = Path("."), json_output: Annotated[bool, typer.Option("--json")] = False, environment: Annotated[str, typer.Option("--environment")] = "development") -> None:
    """Check project files without revealing secrets."""
    project = project.resolve()
    checks = [
        {"name": "python", "ok": sys.version_info >= (3, 11), "detail": sys.version.split()[0]},
        {"name": "pyproject", "ok": (project / "pyproject.toml").is_file(), "detail": "pyproject.toml"},
        {"name": "application", "ok": (project / "app/main.py").is_file(), "detail": "app/main.py"},
        {"name": "environment-template", "ok": (project / ".env.example").is_file(), "detail": ".env.example"},
        {"name": "manifest", "ok": (project / ".smartvinta.json").is_file(), "detail": ".smartvinta.json"},
        {"name": "migrations", "ok": (project / "alembic.ini").is_file(), "detail": "alembic.ini"},
    ]
    if environment == "production":
        checks.append({"name": "production-env", "ok": (project / ".env").is_file(), "detail": ".env required for production validation"})
    ok = all(check["ok"] for check in checks)
    if json_output:
        typer.echo(json.dumps({"ok": ok, "project": str(project), "checks": checks}, indent=2))
    else:
        for check in checks:
            typer.echo(f"{'PASS' if check['ok'] else 'FAIL'} {check['name']}: {check['detail']}")
    if not ok:
        raise typer.Exit(1)

from smartvintaawesomekit.resource_cli import add_resource
app.command("add-resource")(add_resource)

@app.command()
def version(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show toolkit version."""
    typer.echo(json.dumps({"name": "smartvintaawesomekit", "version": __version__}) if json_output else f"smartvintaawesomekit v{__version__}")

__all__ = ["ProjectPlan", "app"]
