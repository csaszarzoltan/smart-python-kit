"""Safe incremental resource generation for generated projects."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Annotated
import typer

_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_TYPES = {"str": ("str", "sample"), "int": ("int", 1), "float": ("float", 1.5), "bool": ("bool", True)}

def _parse_fields(specs: list[str]) -> list[tuple[str, str, bool, object]]:
    result = []
    for spec in specs:
        parts = spec.split(":")
        if len(parts) != 3 or not _NAME.fullmatch(parts[0]) or parts[1] not in _TYPES or parts[2] not in {"required", "optional"}:
            raise typer.BadParameter(f"Invalid field '{spec}'. Use name:str:required.")
        type_name, sample = _TYPES[parts[1]]
        result.append((parts[0], type_name, parts[2] == "required", sample))
    if not result:
        raise typer.BadParameter("At least one --field is required.")
    return result

def add_resource(
    resource: Annotated[str, typer.Argument(help="Singular resource name")],
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    field: Annotated[list[str] | None, typer.Option("--field")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add a tested API vertical slice with preview and conflict protection."""
    if not _NAME.fullmatch(resource):
        raise typer.BadParameter("Resource must be a valid Python identifier.")
    fields = _parse_fields(field or [])
    project = project.resolve()
    plural = resource.lower() + ("es" if resource.lower().endswith("s") else "s")
    route_path = project / "app" / "routes" / f"{plural}.py"
    test_path = project / "tests" / f"test_{plural}.py"
    if route_path.exists() or test_path.exists():
        raise typer.BadParameter(f"Resource '{resource}' already exists.")
    plan = {"resource": resource, "files": [str(route_path.relative_to(project)), str(test_path.relative_to(project))], "dry_run": dry_run}
    if dry_run:
        typer.echo(json.dumps(plan, indent=2) if json_output else "Resource plan\n  " + "\n  ".join(plan["files"]))
        return
    annotations = "\n".join(f"    {name}: {kind}" + ("" if required else " | None = None") for name, kind, required, _ in fields)
    class_name = resource.title().replace("_", "")
    route = (
        "from fastapi import APIRouter, HTTPException\nfrom pydantic import BaseModel\n\n"
        f"router = APIRouter(prefix='/{plural}', tags=['{plural}'])\n_store: dict[int, dict] = {{}}\n\n"
        f"class {class_name}Create(BaseModel):\n{annotations}\n\n"
        f"@router.post('', status_code=201)\nasync def create(payload: {class_name}Create) -> dict:\n"
        "    item_id = len(_store) + 1\n    value = {'id': item_id, **payload.model_dump()}\n    _store[item_id] = value\n    return value\n\n"
        "@router.get('/{item_id}')\nasync def get(item_id: int) -> dict:\n"
        f"    if item_id not in _store:\n        raise HTTPException(status_code=404, detail='{class_name} not found')\n    return _store[item_id]\n"
    )
    sample = {name: value for name, _, _, value in fields}
    test = (
        "from fastapi.testclient import TestClient\nfrom app.main import app\nclient = TestClient(app)\n\n"
        f"def test_{resource}_journey():\n    response = client.post('/{plural}', json={sample!r})\n"
        f"    assert response.status_code == 201\n    assert client.get(f'/{plural}/{{response.json()[\"id\"]}}').status_code == 200\n"
    )
    route_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    route_path.write_text(route)
    test_path.write_text(test)
    main = project / "app" / "main.py"
    content = main.read_text()
    import_line = f"from app.routes.{plural} import router as {plural}_router\n"
    content = import_line + content
    app_pos = content.find("app = FastAPI")
    line_end = content.find("\n", app_pos)
    content = content[:line_end + 1] + f"app.include_router({plural}_router)\n" + content[line_end + 1:]
    main.write_text(content)
    typer.echo(json.dumps({**plan, "dry_run": False}, indent=2) if json_output else f"Added resource '{resource}' with {len(fields)} fields.")
