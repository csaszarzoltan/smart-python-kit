"""User-centered CLI for safe FastAPI project generation and diagnostics."""
from __future__ import annotations

import base64
import difflib
import hashlib
import importlib.util
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
from smartvintaawesomekit.readiness import check_application_import, check_database
from smartvintaawesomekit.resource_cli import add_resource
from smartvintaawesomekit.sdk import freshness as sdk_freshness
from smartvintaawesomekit.sdk import sdk_app

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
        ".smartvinta.json": "",
        "app/__init__.py": "",
        "app/config.py": 'from pydantic_settings import BaseSettings, SettingsConfigDict\n\nclass Settings(BaseSettings):\n    app_name: str = "app"\n    environment: str = "development"\n    database_url: str = "sqlite+aiosqlite:///./dev.db"\n    log_level: str = "INFO"\n    model_config = SettingsConfigDict(env_file=".env", extra="ignore")\n\nsettings = Settings()\n',
        "app/database.py": 'from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine\nfrom sqlalchemy.orm import DeclarativeBase\nfrom app.config import settings\n\nclass Base(DeclarativeBase):\n    """Base class for generated SQLAlchemy models."""\n\nengine = create_async_engine(settings.database_url, pool_pre_ping=True)\nsession_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)\n\nasync def get_db():\n    """Yield one transaction-scoped async database session."""\n    async with session_factory() as session:\n        yield session\n',
        "app/main.py": 'from fastapi import FastAPI\nfrom app.config import settings\nfrom smartvintaawesomekit.observability import install_observability, setup_logging\n\nsetup_logging()\n\napp = FastAPI(title=settings.app_name, version="0.1.0", description="Generated with SmartVintaAwesomeKit")\napp = install_observability(app)\n\n@app.get("/", tags=["system"], summary="Service information")\nasync def root() -> dict[str, str]:\n    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}\n\n@app.get("/health", tags=["system"], summary="Health check")\nasync def health() -> dict[str, str]:\n    return {"status": "healthy", "version": "0.1.0"}\n',
        "tests/__init__.py": "",
        "tests/test_main.py": 'from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_health():\n    response = client.get("/health")\n    assert response.status_code == 200\n    assert response.json()["status"] == "healthy"\n\ndef test_root_guides_user_to_docs():\n    assert client.get("/").json()["docs"] == "/docs"\n',
        "pyproject.toml": f'[build-system]\nrequires = ["setuptools>=68", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "{plan.name}"\nversion = "0.1.0"\nrequires-python = ">=3.11"\ndependencies = ["fastapi>=0.136.0", "uvicorn[standard]>=0.20.0", "sqlalchemy>=2.0", {driver}, "pydantic-settings>=2.0", "smartvintaawesomekit>=0.10.0"]\n\n[project.optional-dependencies]\ndev = ["pytest>=8,<9", "httpx>=0.24", "ruff>=0.3", "alembic>=1.13,<2"]\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        "Dockerfile": 'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install --no-cache-dir .\nCMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n',
        "README.md": f'# {plan.name}\n\nGenerated with SmartVintaAwesomeKit {__version__}, preset **{plan.preset}**, database **{plan.database}**.\n\n## Quick start\n\n```bash\ncp .env.example .env\npython -m venv .venv\n. .venv/bin/activate\npip install -e ".[dev]"\npytest\nuvicorn app.main:app --reload\n```\n\nOpen <http://127.0.0.1:8000/docs>. Run `smartvintaawesomekit doctor --project .` before deployment. Never commit real secrets.\n',
    }
    files.update({
        ".github/workflows/quality.yml": "name: quality\non: [push, pull_request]\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - run: pip install -e '.[dev]'\n      - run: python scripts/check.py\n",
        "scripts/check.py": "\"\"\"Run the same quality checks locally and in CI.\"\"\"\nimport subprocess\nimport sys\n\nCOMMANDS = [[sys.executable, '-m', 'pytest', '-q'], ['ruff', 'check', '.']]\nfor command in COMMANDS:\n    result = subprocess.run(command, check=False)\n    if result.returncode:\n        raise SystemExit(result.returncode)\n",
    })

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
    managed = {
        name: {
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "baseline": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        }
        for name, content in files.items()
        if name != ".smartvinta.json"
    }
    files[".smartvinta.json"] = json.dumps({
        "schema_version": 1,
        "generator": "smartvintaawesomekit",
        "generator_version": __version__,
        "preset": plan.preset,
        "database": plan.database,
        "managed_files": managed,
        "resources": {},
    }, indent=2) + "\n"
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
def doctor(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
    environment: Annotated[str, typer.Option("--environment")] = "development",
    connectivity: Annotated[bool, typer.Option("--connectivity")] = False,
    startup: Annotated[bool, typer.Option("--startup")] = False,
    sdk: Annotated[bool, typer.Option("--sdk")] = False,
) -> None:
    """Check project structure, security, connectivity, and startup readiness."""
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
        env_path = project / ".env"
        checks.append({"name": "production-env", "ok": env_path.is_file(), "detail": ".env required for production validation"})
        env_text = env_path.read_text(encoding="utf-8") if env_path.is_file() else ""
        secret = next((line.split("=", 1)[1].strip() for line in env_text.splitlines() if line.startswith("AUTH_JWT_SECRET_KEY=")), "")
        secret_ok = len(secret) >= 32 and secret.lower() not in {"change-me", "changeme", "secret", "your-secret-key"}
        checks.append({"name": "jwt-secret", "ok": secret_ok, "detail": "AUTH_JWT_SECRET_KEY must be a non-placeholder value of at least 32 characters"})
    if connectivity:
        checks.append(check_database(project))
    if startup:
        checks.append(check_application_import(project))
    if sdk:
        checks.append(sdk_freshness(project))
    checks.extend([
        {"name": "optional-redis", "ok": importlib.util.find_spec("redis") is not None, "detail": "installed" if importlib.util.find_spec("redis") else "install smartvintaawesomekit[redis] when Redis is selected", "blocking": False},
        {"name": "optional-alembic", "ok": importlib.util.find_spec("alembic") is not None, "detail": "installed" if importlib.util.find_spec("alembic") else "install alembic to run migrations", "blocking": False},
    ])
    ok = all(check["ok"] for check in checks if check.get("blocking", True))
    if json_output:
        typer.echo(json.dumps({"ok": ok, "project": str(project), "checks": checks}, indent=2))
    else:
        for check in checks:
            typer.echo(f"{'PASS' if check['ok'] else 'FAIL'} {check['name']}: {check['detail']}")
    if not ok:
        raise typer.Exit(1)

app.command("add-resource")(add_resource)
app.add_typer(sdk_app, name="sdk")

@app.command()
def inspect(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    check: Annotated[bool, typer.Option("--check")] = False,
    diff: Annotated[bool, typer.Option("--diff", help="Include safe unified diffs")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Report scaffold provenance, drift, and optional safe text diffs."""
    project = project.resolve()
    manifest_path = project / ".smartvinta.json"
    if not manifest_path.is_file():
        raise typer.BadParameter("No .smartvinta.json manifest found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version", 0) not in {0, 1}:
        raise typer.BadParameter("Unsupported manifest schema version.")
    managed = manifest.get("managed_files", {})
    missing, modified, diffs = [], [], {}
    for relative, metadata in managed.items():
        path = project / relative
        expected = metadata.get("sha256") if isinstance(metadata, dict) else metadata
        if not path.is_file():
            missing.append(relative)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            modified.append(relative)
            if diff and isinstance(metadata, dict) and metadata.get("baseline"):
                try:
                    baseline = base64.b64decode(metadata["baseline"]).decode("utf-8").splitlines()
                    current = path.read_text(encoding="utf-8").splitlines()
                    diffs[relative] = "\n".join(difflib.unified_diff(baseline, current, fromfile=f"generated/{relative}", tofile=f"current/{relative}", lineterm=""))
                except (UnicodeDecodeError, ValueError):
                    diffs[relative] = "Diff unavailable for non-text content."
    payload = {
        "schema_version": manifest.get("schema_version", 0),
        "status": "clean" if not missing and not modified else "drifted",
        "generator_version": manifest.get("generator_version"),
        "preset": manifest.get("preset"),
        "database": manifest.get("database"),
        "resources": sorted(manifest.get("resources", {})),
        "missing_files": sorted(missing),
        "modified_files": sorted(modified),
        "diffs": diffs,
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo(f"Status: {payload['status']}")
        typer.echo(f"Generator: {payload['generator_version']}; preset: {payload['preset']}; database: {payload['database']}")
        for name in payload["missing_files"]:
            typer.echo(f"MISSING {name} | restore or regenerate the file")
        for name in payload["modified_files"]:
            typer.echo(f"MODIFIED {name} | review diff or accept intentional changes")
            if name in diffs:
                typer.echo(diffs[name])
    if check and payload["status"] != "clean":
        raise typer.Exit(1)


@app.command("manifest-accept")
def manifest_accept(
    paths: Annotated[list[str], typer.Argument(help="Managed relative paths to accept")],
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Accept intentional changes to selected managed text files."""
    project = project.resolve()
    manifest_path = project / ".smartvinta.json"
    if not manifest_path.is_file():
        raise typer.BadParameter("No .smartvinta.json manifest found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    managed = manifest.get("managed_files", {})
    sensitive = {".env", ".env.local"}
    accepted = []
    for relative in paths:
        if relative in sensitive or relative.startswith(".env.") or "secret" in relative.lower():
            raise typer.BadParameter(f"Sensitive file '{relative}' cannot be managed or accepted.")
        if relative not in managed:
            raise typer.BadParameter(f"'{relative}' is not a generator-managed file.")
        target = (project / relative).resolve()
        if project not in target.parents or not target.is_file():
            raise typer.BadParameter(f"Managed file '{relative}' does not exist safely inside the project.")
        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise typer.BadParameter(f"Binary file '{relative}' cannot be accepted.") from exc
        accepted.append((relative, content))
    payload = {"dry_run": dry_run, "accepted_files": [item[0] for item in accepted]}
    if not dry_run:
        backup = manifest_path.with_suffix(".json.bak")
        backup.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
        for relative, content in accepted:
            managed[relative] = {
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "baseline": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            }
        manifest["schema_version"] = 1
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    typer.echo(json.dumps(payload, indent=2) if json_output else ("Would accept: " if dry_run else "Accepted: ") + ", ".join(payload["accepted_files"]))


@app.command("upgrade-plan")
def upgrade_plan(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    check: Annotated[bool, typer.Option("--check")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a read-only upgrade plan and classify local conflicts."""
    project = project.resolve()
    manifest_path = project / ".smartvinta.json"
    if not manifest_path.is_file():
        raise typer.BadParameter("No .smartvinta.json manifest found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = manifest.get("schema_version", 0)
    if schema not in {0, 1}:
        raise typer.BadParameter("Unsupported manifest schema version.")
    conflicts, missing = [], []
    for relative, metadata in manifest.get("managed_files", {}).items():
        target = project / relative
        expected = metadata.get("sha256") if isinstance(metadata, dict) else metadata
        if not target.is_file():
            missing.append(relative)
        elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            conflicts.append(relative)
    project_version = manifest.get("generator_version", "unknown")
    current = project_version == __version__
    if conflicts or missing:
        status = "conflicts"
    elif current:
        status = "current"
    else:
        status = "upgrade_available"
    payload = {
        "status": status,
        "project_version": project_version,
        "available_version": __version__,
        "safe_actions": [] if current or conflicts or missing else ["regenerate-managed-files"],
        "conflicts": sorted(conflicts),
        "missing_files": sorted(missing),
        "manual_actions": ["review conflicts before any upgrade"] if conflicts or missing else [],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo(f"Upgrade status: {status}")
        typer.echo(f"Project: {project_version}; available: {__version__}")
        for path in payload["conflicts"]:
            typer.echo(f"CONFLICT {path} | inspect --diff before upgrading")
        for path in payload["missing_files"]:
            typer.echo(f"MISSING {path} | restore or regenerate before upgrading")
    if check and status == "conflicts":
        raise typer.Exit(1)


@app.command("upgrade-apply")
def upgrade_apply(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Safely apply current templates only when managed files have not drifted."""
    project = project.resolve()
    manifest_path = project / ".smartvinta.json"
    if not manifest_path.is_file():
        raise typer.BadParameter("No .smartvinta.json manifest found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version", 0) not in {0, 1}:
        raise typer.BadParameter("Unsupported manifest schema version.")
    managed = manifest.get("managed_files", {})
    conflicts: list[str] = []
    missing: list[str] = []
    for relative, metadata in managed.items():
        target = project / relative
        expected = metadata.get("sha256") if isinstance(metadata, dict) else metadata
        if not target.is_file():
            missing.append(relative)
        elif hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            conflicts.append(relative)
    if conflicts or missing:
        payload = {
            "status": "conflicts",
            "dry_run": dry_run,
            "updated_files": [],
            "conflicts": sorted(conflicts),
            "missing_files": sorted(missing),
        }
        typer.echo(json.dumps(payload, indent=2) if json_output else "Upgrade blocked by managed-file drift.")
        raise typer.Exit(1)

    plan = ProjectPlan(
        project.name,
        project,
        str(manifest.get("preset", "api")),
        str(manifest.get("database", "sqlite")),
    )
    templates = _project_files(plan)
    templates.pop(".smartvinta.json", None)
    updated: dict[str, str] = {}
    for relative, content in templates.items():
        target = project / relative
        if relative not in managed and target.exists():
            conflicts.append(relative)
        elif not target.exists() or target.read_text(encoding="utf-8") != content:
            updated[relative] = content
    if conflicts:
        payload = {"status": "conflicts", "dry_run": dry_run, "updated_files": [],
                   "conflicts": sorted(conflicts), "missing_files": []}
        typer.echo(json.dumps(payload, indent=2) if json_output else "Upgrade blocked by unmanaged path conflicts.")
        raise typer.Exit(1)

    payload = {
        "status": "preview" if dry_run else "applied",
        "dry_run": dry_run,
        "from_version": manifest.get("generator_version", "unknown"),
        "to_version": __version__,
        "updated_files": sorted(updated),
        "conflicts": [],
        "missing_files": [],
    }
    if dry_run:
        typer.echo(json.dumps(payload, indent=2) if json_output else "Would update: " + ", ".join(sorted(updated)))
        return

    backup = project / ".smartvinta.json.upgrade.bak"
    backup.write_bytes(manifest_path.read_bytes())
    with tempfile.TemporaryDirectory(prefix="smartvinta-upgrade-") as temp:
        stage = Path(temp)
        for relative, content in updated.items():
            staged = stage / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(content, encoding="utf-8")
        for relative in sorted(updated):
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stage / relative, target)
    for relative in templates:
        target = project / relative
        if not target.is_file():
            continue
        data = target.read_bytes()
        managed[relative] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "baseline": base64.b64encode(data).decode("ascii"),
        }
    manifest["schema_version"] = 1
    manifest["generator_version"] = __version__
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    typer.echo(json.dumps(payload, indent=2) if json_output else "Updated: " + ", ".join(sorted(updated)))


@app.command("manifest-repair")
def manifest_repair(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Repair supported manifest metadata without accepting file drift."""
    project = project.resolve()
    manifest_path = project / ".smartvinta.json"
    if not manifest_path.is_file():
        raise typer.BadParameter("No .smartvinta.json manifest found.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter("Manifest is not valid JSON and requires manual recovery.") from exc
    schema = manifest.get("schema_version")
    if schema not in {None, 0, 1}:
        raise typer.BadParameter("Unsupported newer manifest schema; upgrade the toolkit before repair.")
    changes = []
    if schema != 1:
        changes.append("set schema_version to 1")
    if not isinstance(manifest.get("resources", {}), dict):
        changes.append("reset invalid resources metadata")
    payload = {"dry_run": dry_run, "changes": changes}
    if not dry_run and changes:
        backup = manifest_path.with_suffix(".json.bak")
        backup.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
        manifest["schema_version"] = 1
        if not isinstance(manifest.get("resources", {}), dict):
            manifest["resources"] = {}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo("No repair needed." if not changes else ("Would repair: " if dry_run else "Repaired: ") + "; ".join(changes))



@app.command()
def migrate(
    action: Annotated[str, typer.Argument(help="upgrade, downgrade, current, or history")],
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    revision: Annotated[str, typer.Option("--revision")] = "head",
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run or preview an Alembic migration command without using a shell."""
    actions = {"upgrade", "downgrade", "current", "history"}
    if action not in actions:
        raise typer.BadParameter(f"Unknown action '{action}'. Choose from: {', '.join(sorted(actions))}.")
    if not re.fullmatch(r"[A-Za-z0-9_+@-]+", revision):
        raise typer.BadParameter("Revision contains unsafe characters.")
    project = project.resolve()
    if not (project / "alembic.ini").is_file():
        raise typer.BadParameter("No alembic.ini found in the project.")
    command = ["alembic", action]
    if action in {"upgrade", "downgrade"}:
        command.append(revision)
    payload = {"project": str(project), "command": command, "executed": not dry_run}
    if dry_run:
        typer.echo(json.dumps(payload, indent=2) if json_output else "Would run: " + " ".join(command))
        return
    import subprocess
    result = subprocess.run(command, cwd=project, check=False)
    if json_output:
        payload["returncode"] = result.returncode
        typer.echo(json.dumps(payload, indent=2))
    if result.returncode:
        raise typer.Exit(result.returncode)

@app.command()
def version(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show toolkit version."""
    typer.echo(json.dumps({"name": "smartvintaawesomekit", "version": __version__}) if json_output else f"smartvintaawesomekit v{__version__}")

__all__ = ["ProjectPlan", "app"]
