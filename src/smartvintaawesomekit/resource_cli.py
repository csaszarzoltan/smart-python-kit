"""Safe persistent vertical-slice generation for generated projects."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Annotated, Any

import typer

_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_TYPES: dict[str, tuple[str, str, str, object]] = {
    "str": ("str", "String(255)", "sa.String(length=255)", "sample"),
    "int": ("int", "Integer", "sa.Integer()", 1),
    "float": ("float", "Float", "sa.Float()", 1.5),
    "bool": ("bool", "Boolean", "sa.Boolean()", True),
}
Field = tuple[str, str, bool, object, str, str]


def _parse_fields(specs: list[str]) -> list[Field]:
    """Validate CLI field specifications and return generation metadata."""
    result: list[Field] = []
    seen: set[str] = set()
    for spec in specs:
        parts = spec.split(":")
        if (len(parts) != 3 or not _NAME.fullmatch(parts[0]) or parts[1] not in _TYPES
                or parts[2] not in {"required", "optional"}):
            raise typer.BadParameter(f"Invalid field '{spec}'. Use name:str:required.")
        if parts[0] in {"id", "created_at", "updated_at"}:
            raise typer.BadParameter(f"Field '{parts[0]}' is reserved.")
        if parts[0] in seen:
            raise typer.BadParameter(f"Duplicate field '{parts[0]}'.")
        seen.add(parts[0])
        py_type, orm_type, migration_type, sample = _TYPES[parts[1]]
        result.append((parts[0], py_type, parts[2] == "required", sample, orm_type, migration_type))
    if not result:
        raise typer.BadParameter("At least one --field is required.")
    return result


def _plural(resource: str) -> str:
    return resource.lower() + ("es" if resource.lower().endswith("s") else "s")


def _class_name(resource: str) -> str:
    return resource.title().replace("_", "")


def _render_files(resource: str, fields: list[Field], revision: str) -> dict[str, str]:
    plural = _plural(resource)
    cls = _class_name(resource)
    model_columns = "\n".join(
        f"    {name}: Mapped[{kind}{'' if required else ' | None'}] = mapped_column({orm}, nullable={not required})"
        for name, kind, required, _sample, orm, _migration in fields
    )
    create_fields = "\n".join(
        f"    {name}: {kind}" + ("" if required else " | None = None")
        for name, kind, required, _sample, _orm, _migration in fields
    )
    update_fields = "\n".join(
        f"    {name}: {kind} | None = None"
        for name, kind, _required, _sample, _orm, _migration in fields
    )
    read_fields = "\n".join(
        f"    {name}: {kind}" + ("" if required else " | None")
        for name, kind, required, _sample, _orm, _migration in fields
    )
    migration_columns = ",\n".join(
        f"        sa.Column({name!r}, {migration}, nullable={not required})"
        for name, _kind, required, _sample, _orm, migration in fields
    )
    sample = {name: value for name, _kind, _required, value, _orm, _migration in fields}
    update_name = fields[0][0]
    update_value: Any = fields[0][3]
    if isinstance(update_value, str):
        update_value = "updated"
    elif isinstance(update_value, bool):
        update_value = not update_value
    elif isinstance(update_value, (int, float)):
        update_value += 1

    model = f'''"""Persistent {resource} database model."""\nfrom __future__ import annotations\n\nfrom datetime import datetime\nfrom sqlalchemy import Boolean, Float, Integer, String, func\nfrom sqlalchemy.orm import Mapped, mapped_column\nfrom app.database import Base\n\n\nclass {cls}(Base):\n    """Persisted {resource} entity."""\n\n    __tablename__ = "{plural}"\n\n    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)\n{model_columns}\n    created_at: Mapped[datetime] = mapped_column(server_default=func.now())\n    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())\n'''
    schemas = f'''"""Validated {resource} API schemas."""\nfrom __future__ import annotations\n\nfrom pydantic import BaseModel, ConfigDict\n\n\nclass {cls}Create(BaseModel):\n    """Fields accepted when creating a {resource}."""\n\n{create_fields}\n\n\nclass {cls}Update(BaseModel):\n    """Optional fields accepted for partial updates."""\n\n{update_fields}\n\n\nclass {cls}Read(BaseModel):\n    """Public representation of a persisted {resource}."""\n\n    model_config = ConfigDict(from_attributes=True)\n    id: int\n{read_fields}\n'''
    service = f'''"""Database operations for {resource} resources."""\nfrom __future__ import annotations\n\nfrom sqlalchemy import select\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom app.models.{plural} import {cls}\nfrom app.schemas.{plural} import {cls}Create, {cls}Update\n\n\nclass {cls}Service:\n    """Transaction-safe CRUD service for {resource} entities."""\n\n    @staticmethod\n    async def create(db: AsyncSession, payload: {cls}Create) -> {cls}:\n        item = {cls}(**payload.model_dump())\n        db.add(item)\n        await db.commit()\n        await db.refresh(item)\n        return item\n\n    @staticmethod\n    async def list(db: AsyncSession, offset: int = 0, limit: int = 100) -> list[{cls}]:\n        result = await db.execute(select({cls}).offset(offset).limit(limit))\n        return list(result.scalars().all())\n\n    @staticmethod\n    async def get(db: AsyncSession, item_id: int) -> {cls} | None:\n        return await db.get({cls}, item_id)\n\n    @staticmethod\n    async def update(db: AsyncSession, item: {cls}, payload: {cls}Update) -> {cls}:\n        for name, value in payload.model_dump(exclude_unset=True).items():\n            setattr(item, name, value)\n        await db.commit()\n        await db.refresh(item)\n        return item\n\n    @staticmethod\n    async def delete(db: AsyncSession, item: {cls}) -> None:\n        await db.delete(item)\n        await db.commit()\n'''
    route = f'''"""Persistent CRUD endpoints for {plural}."""\nfrom __future__ import annotations\n\nfrom typing import Annotated\nfrom fastapi import APIRouter, Depends, HTTPException, Query, Response, status\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom app.database import get_db\nfrom app.schemas.{plural} import {cls}Create, {cls}Read, {cls}Update\nfrom app.services.{plural} import {cls}Service\n\nrouter = APIRouter(prefix="/{plural}", tags=["{plural}"])\nDb = Annotated[AsyncSession, Depends(get_db)]\n\n@router.post("", response_model={cls}Read, status_code=status.HTTP_201_CREATED)\nasync def create_{resource}(payload: {cls}Create, db: Db) -> {cls}Read:\n    """Create and persist a {resource}."""\n    return await {cls}Service.create(db, payload)\n\n@router.get("", response_model=list[{cls}Read])\nasync def list_{plural}(db: Db, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 100) -> list[{cls}Read]:\n    """List persisted {plural} with bounded pagination."""\n    return await {cls}Service.list(db, offset, limit)\n\n@router.get("/{{item_id}}", response_model={cls}Read)\nasync def get_{resource}(item_id: int, db: Db) -> {cls}Read:\n    """Return one {resource} or a friendly 404."""\n    item = await {cls}Service.get(db, item_id)\n    if item is None:\n        raise HTTPException(status_code=404, detail="{cls} not found")\n    return item\n\n@router.patch("/{{item_id}}", response_model={cls}Read)\nasync def update_{resource}(item_id: int, payload: {cls}Update, db: Db) -> {cls}Read:\n    """Partially update a persisted {resource}."""\n    item = await {cls}Service.get(db, item_id)\n    if item is None:\n        raise HTTPException(status_code=404, detail="{cls} not found")\n    return await {cls}Service.update(db, item, payload)\n\n@router.delete("/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)\nasync def delete_{resource}(item_id: int, db: Db) -> Response:\n    """Delete a persisted {resource}."""\n    item = await {cls}Service.get(db, item_id)\n    if item is None:\n        raise HTTPException(status_code=404, detail="{cls} not found")\n    await {cls}Service.delete(db, item)\n    return Response(status_code=status.HTTP_204_NO_CONTENT)\n'''
    migration = f'''"""Create {plural} table.\n\nRevision ID: {revision}\n"""\nfrom alembic import op\nimport sqlalchemy as sa\n\nrevision = "{revision}"\ndown_revision = None\nbranch_labels = None\ndepends_on = None\n\ndef upgrade() -> None:\n    """Create the {plural} table."""\n    op.create_table(\n        "{plural}",\n        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),\n{migration_columns},\n        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),\n        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),\n    )\n\ndef downgrade() -> None:\n    """Drop the {plural} table."""\n    op.drop_table("{plural}")\n'''
    test = f'''"""Integration tests for persistent {plural}."""\nimport asyncio\nfrom fastapi.testclient import TestClient\nfrom app.database import Base, engine\nfrom app.main import app\n\nasync def _reset_database() -> None:\n    async with engine.begin() as connection:\n        await connection.run_sync(Base.metadata.drop_all)\n        await connection.run_sync(Base.metadata.create_all)\n\ndef test_{resource}_crud_journey() -> None:\n    asyncio.run(_reset_database())\n    with TestClient(app) as client:\n        created = client.post("/{plural}", json={sample!r})\n        assert created.status_code == 201, created.text\n        item_id = created.json()["id"]\n        assert client.get(f"/{plural}/{{item_id}}").status_code == 200\n        assert len(client.get("/{plural}").json()) == 1\n        updated = client.patch(f"/{plural}/{{item_id}}", json={{{update_name!r}: {update_value!r}}})\n        assert updated.status_code == 200\n        assert updated.json()[{update_name!r}] == {update_value!r}\n        assert client.delete(f"/{plural}/{{item_id}}").status_code == 204\n        assert client.get(f"/{plural}/{{item_id}}").status_code == 404\n\ndef test_{resource}_validation_and_missing_paths() -> None:\n    with TestClient(app) as client:\n        assert client.get("/{plural}/999999").status_code == 404\n        assert client.get("/{plural}?limit=101").status_code == 422\n'''
    return {
        f"app/models/{plural}.py": model,
        f"app/schemas/{plural}.py": schemas,
        f"app/services/{plural}.py": service,
        f"app/routes/{plural}.py": route,
        f"migrations/versions/{revision}_create_{plural}.py": migration,
        f"tests/test_{plural}.py": test,
    }


def add_resource(
    resource: Annotated[str, typer.Argument(help="Singular resource name")],
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    field: Annotated[list[str] | None, typer.Option("--field")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Generate a persistent model/schema/service/CRUD/migration/test vertical slice."""
    if not _NAME.fullmatch(resource):
        raise typer.BadParameter("Resource must be a valid Python identifier.")
    fields = _parse_fields(field or [])
    project = project.resolve()
    manifest_path = project / ".smartvinta.json"
    if not manifest_path.is_file():
        raise typer.BadParameter("No .smartvinta.json manifest found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    revision = f"{len(manifest.get('resources', {})) + 1:04d}"
    generated = _render_files(resource, fields, revision)
    paths = [project / relative for relative in generated]
    main = project / "app/main.py"
    all_paths = [*paths, main]
    conflicts = [str(path.relative_to(project)) for path in all_paths[:-1] if path.exists()]
    if conflicts:
        raise typer.BadParameter(f"Resource '{resource}' already exists: {', '.join(conflicts)}")
    plan = {"resource": resource, "files": sorted(generated), "dry_run": dry_run, "persistence": "sqlalchemy"}
    if dry_run:
        typer.echo(json.dumps(plan, indent=2) if json_output else "Resource plan\n  " + "\n  ".join(plan["files"]))
        return

    for package in ("models", "schemas", "services"):
        init = project / "app" / package / "__init__.py"
        init.parent.mkdir(parents=True, exist_ok=True)
        init.touch(exist_ok=True)
    for relative, content in generated.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    plural = _plural(resource)
    content = main.read_text(encoding="utf-8")
    import_line = f"from app.routes.{plural} import router as {plural}_router\n"
    if import_line not in content:
        content = import_line + content
    marker = "app = FastAPI"
    app_pos = content.find(marker)
    line_end = content.find("\n", app_pos)
    include = f"app.include_router({plural}_router)\n"
    if include not in content:
        content = content[:line_end + 1] + include + content[line_end + 1:]
    main.write_text(content, encoding="utf-8")

    managed = manifest.setdefault("managed_files", {})
    for path in all_paths:
        data = path.read_bytes()
        relative = str(path.relative_to(project))
        managed[relative] = {"sha256": hashlib.sha256(data).hexdigest(),
                             "baseline": base64.b64encode(data).decode("ascii")}
    manifest["schema_version"] = 1
    manifest.setdefault("resources", {})[resource] = {
        "fields": field or [], "persistence": "sqlalchemy", "files": sorted(generated)
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    typer.echo(json.dumps({**plan, "dry_run": False}, indent=2) if json_output
               else f"Added persistent resource '{resource}' with {len(fields)} fields.")
