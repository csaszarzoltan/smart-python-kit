"""Deterministic OpenAPI contract and TypeScript SDK lifecycle."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

sdk_app = typer.Typer(help="Generate and verify typed clients from a FastAPI contract.")


def _contract(project: Path) -> dict[str, Any]:
    """Load a project's OpenAPI document in an isolated subprocess."""
    code = "import json; from app.main import app; print(json.dumps(app.openapi(), sort_keys=True))"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(project), os.environ.get("PYTHONPATH", "")])
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=project, env=environment,
            capture_output=True, text=True, timeout=15, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Application contract import timed out") from exc
    if result.returncode:
        raise RuntimeError("Application contract import failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Application produced an invalid OpenAPI contract") from exc


def _canonical(contract: dict[str, Any]) -> bytes:
    """Serialize an OpenAPI document deterministically for hashing."""
    return (json.dumps(contract, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _method_name(method: str, path: str) -> str:
    """Create a stable camel-case TypeScript operation name."""
    parts = [part for part in path.split("/") if part and not part.startswith("{")]
    noun = parts[-1] if parts else "root"
    singular = noun[:-1] if noun.endswith("s") else noun
    verb = {"post": "create", "put": "replace", "patch": "update", "delete": "delete"}.get(method, "get")
    target = singular if method != "get" or "{" in path else noun
    words = re.split(r"[^A-Za-z0-9]+", verb + " " + target)
    return words[0].lower() + "".join(word.title() for word in words[1:] if word)


def _schema_type(schema: dict[str, Any]) -> str:
    """Map an OpenAPI schema fragment to a TypeScript type."""
    if "$ref" in schema:
        return str(schema["$ref"]).rsplit("/", 1)[-1]
    if "anyOf" in schema:
        return " | ".join(dict.fromkeys(_schema_type(item) for item in schema["anyOf"]))
    schema_type = schema.get("type")
    if schema_type == "array":
        return f"{_schema_type(schema.get('items', {}))}[]"
    return {"string": "string", "integer": "number", "number": "number",
            "boolean": "boolean", "null": "null", "object": "Record<string, unknown>"}.get(
        schema_type, "unknown"
    )


def _interfaces(contract: dict[str, Any]) -> str:
    """Render OpenAPI component objects as deterministic TypeScript interfaces."""
    rendered: list[str] = []
    schemas = contract.get("components", {}).get("schemas", {})
    for name, schema in sorted(schemas.items()):
        if schema.get("type") != "object" and "properties" not in schema:
            continue
        required = set(schema.get("required", []))
        fields = []
        for field, definition in sorted(schema.get("properties", {}).items()):
            optional = "" if field in required else "?"
            fields.append(f"  {field}{optional}: {_schema_type(definition)};")
        rendered.append(f"export interface {name} {{\n" + "\n".join(fields) + "\n}")
    return "\n\n".join(rendered)


def _operation_schema(operation: dict[str, Any], section: str) -> dict[str, Any]:
    """Return the JSON schema for an operation request or successful response."""
    if section == "requestBody":
        return operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    responses = operation.get("responses", {})
    successful = next((value for code, value in sorted(responses.items()) if str(code).startswith("2")), {})
    return successful.get("content", {}).get("application/json", {}).get("schema", {})


def _typescript(contract: dict[str, Any], digest: str) -> str:
    """Render a dependency-free TypeScript fetch client from OpenAPI paths."""
    methods: list[str] = []
    supported = {"get", "post", "put", "patch", "delete"}
    for path, operations in sorted(contract.get("paths", {}).items()):
        for method, operation in sorted(operations.items()):
            if method not in supported:
                continue
            name = _method_name(method, path)
            path_params = re.findall(r"{([^}]+)}", path)
            params = [f"{item}: string | number" for item in path_params]
            has_body = "requestBody" in operation
            if has_body:
                params.append(f"body: {_schema_type(_operation_schema(operation, 'requestBody'))}")
            params.append("options: RequestInit = {}")
            expression = path
            for item in path_params:
                expression = expression.replace("{" + item + "}", "${encodeURIComponent(String(" + item + "))}")
            body = "\n      body: JSON.stringify(body)," if has_body else ""
            content_type = "\n      headers: { 'content-type': 'application/json', ...options.headers }," if has_body else ""
            response_type = _schema_type(_operation_schema(operation, "response"))
            methods.append(
                f"  async {name}({', '.join(params)}): Promise<{response_type}> {{\n"
                f"    return this.request(`{expression}`, {{ ...options, method: '{method.upper()}',{content_type}{body} }});\n"
                "  }"
            )
    joined = "\n\n".join(methods)
    interfaces = _interfaces(contract)
    return f'''/* Generated by SmartVintaAwesomeKit. OpenAPI SHA-256: {digest} */
{interfaces}

export class ApiError extends Error {{
  constructor(public readonly status: number, public readonly payload: unknown) {{
    super(`API request failed with status ${{status}}`);
  }}
}}

export class ApiClient {{
  constructor(private readonly baseUrl: string, private readonly fetcher: typeof fetch = fetch) {{}}

  private async request(path: string, init: RequestInit): Promise<unknown> {{
    const response = await this.fetcher(`${{this.baseUrl}}${{path}}`, init);
    const text = await response.text();
    const payload: unknown = text ? JSON.parse(text) : null;
    if (!response.ok) throw new ApiError(response.status, payload);
    return payload;
  }}

{joined}
}}
'''

def _python_type(schema: dict[str, Any]) -> str:
    """Map an OpenAPI schema fragment to a Python type expression."""
    if "$ref" in schema:
        return str(schema["$ref"]).rsplit("/", 1)[-1]
    if "anyOf" in schema:
        return " | ".join(dict.fromkeys(_python_type(item) for item in schema["anyOf"]))
    if schema.get("type") == "array":
        return f"list[{_python_type(schema.get('items', {}))}]"
    return {"string": "str", "integer": "int", "number": "float", "boolean": "bool",
            "null": "None", "object": "dict[str, object]"}.get(schema.get("type"), "object")


def _python_client(contract: dict[str, Any], digest: str) -> str:
    """Render a dependency-free synchronous Python client from OpenAPI."""
    models: list[str] = []
    for name, schema in sorted(contract.get("components", {}).get("schemas", {}).items()):
        if schema.get("type") != "object" and "properties" not in schema:
            continue
        required = set(schema.get("required", []))
        fields: list[str] = []
        for field, definition in sorted(schema.get("properties", {}).items()):
            annotation = _python_type(definition)
            if field not in required and "None" not in annotation:
                annotation += " | None"
            fields.append(f"    {field}: {annotation}")
        models.append(f"class {name}(TypedDict):\n" + ("\n".join(fields) or "    pass"))
    methods: list[str] = []
    for path, operations in sorted(contract.get("paths", {}).items()):
        for method, operation in sorted(operations.items()):
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            name = re.sub(r"(?<!^)(?=[A-Z])", "_", _method_name(method, path)).lower()
            path_params = re.findall(r"{([^}]+)}", path)
            params = [f"{item}: str | int" for item in path_params]
            has_body = "requestBody" in operation
            if has_body:
                params.append(f"body: {_python_type(_operation_schema(operation, 'requestBody'))}")
            expression = path
            for item in path_params:
                expression = expression.replace("{" + item + "}", "{quote(str(" + item + "), safe='')}")
            body_arg = ", body" if has_body else ""
            response = _python_type(_operation_schema(operation, "response"))
            methods.append(
                f"    def {name}(self, {', '.join(params)}) -> {response}:\n"
                f"        return self._request('{method.upper()}', f'{expression}'{body_arg})  # type: ignore[return-value]"
            )
    return f'''"""Generated SmartVintaAwesomeKit client. OpenAPI SHA-256: {digest}."""
from __future__ import annotations

import json
from typing import TypedDict
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

{chr(10).join(models)}

class ApiError(RuntimeError):
    """HTTP failure returned by the API."""
    def __init__(self, status: int, payload: object) -> None:
        super().__init__(f"API request failed with status {{status}}")
        self.status = status
        self.payload = payload

class ApiClient:
    """Small standard-library API client."""
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: object | None = None) -> object:
        data = json.dumps(body).encode() if body is not None else None
        request = Request(self.base_url + path, data=data, method=method,
                          headers={{"content-type": "application/json"}} if data else {{}})
        try:
            with urlopen(request) as response:  # noqa: S310
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            raw = exc.read()
            raise ApiError(exc.code, json.loads(raw) if raw else None) from exc

{chr(10).join(methods)}
'''


def _paths(project: Path, language: str = "typescript") -> tuple[Path, Path, Path]:
    directory = project / "sdk" / language
    return directory / ("client.py" if language == "python" else "client.ts"), directory / "openapi.json", directory / "openapi-lock.json"


@sdk_app.command("generate")
def generate(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    language: Annotated[str, typer.Option("--language")] = "typescript",
) -> None:
    """Generate a deterministic TypeScript client and locked OpenAPI contract."""
    project = project.resolve()
    if language not in {"typescript", "python"}:
        raise typer.BadParameter("language must be typescript or python")
    try:
        contract = _contract(project)
    except RuntimeError:
        payload = {"status": "error", "code": "openapi_import_failed",
                   "remediation": "Run the application locally and inspect startup logs"}
        typer.echo(json.dumps(payload, indent=2) if json_output else payload["remediation"])
        raise typer.Exit(1) from None
    canonical = _canonical(contract)
    digest = hashlib.sha256(canonical).hexdigest()
    client_path, contract_path, lock_path = _paths(project, language)
    payload = {"status": "preview" if dry_run else "generated", "dry_run": dry_run, "language": language,
               "openapi_sha256": digest,
               "files": [str(path.relative_to(project)) for path in (client_path, contract_path, lock_path)]}
    if not dry_run:
        client_path.parent.mkdir(parents=True, exist_ok=True)
        client_content = _python_client(contract, digest) if language == "python" else _typescript(contract, digest)
        client_path.write_text(client_content, encoding="utf-8")
        contract_path.write_bytes(canonical)
        lock_path.write_text(json.dumps({"schema_version": 1, "openapi_sha256": digest,
                                         "client_sha256": hashlib.sha256(client_content.encode()).hexdigest(),
                                         "generator": "smartvintaawesomekit"}, indent=2) + "\n",
                             encoding="utf-8")
    typer.echo(json.dumps(payload, indent=2) if json_output else f"SDK {payload['status']}: {digest}")


def freshness(project: Path) -> dict[str, Any]:
    """Return a readiness check for the committed TypeScript SDK contract."""
    project = project.resolve()
    client_path, _contract_path, lock_path = _paths(project)
    if not lock_path.is_file() or not client_path.is_file():
        return {"name": "sdk-freshness", "ok": False, "blocking": True,
                "code": "sdk_missing", "detail": "SDK contract lock is missing",
                "remediation": "Run smartvintaawesomekit sdk generate --project ."}
    try:
        current = hashlib.sha256(_canonical(_contract(project))).hexdigest()
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        locked = lock.get("openapi_sha256")
        client_locked = lock.get("client_sha256")
        client_current = hashlib.sha256(client_path.read_bytes()).hexdigest()
    except (RuntimeError, OSError, json.JSONDecodeError):
        return {"name": "sdk-freshness", "ok": False, "blocking": True,
                "code": "sdk_check_failed", "detail": "SDK freshness could not be verified",
                "remediation": "Verify application startup, then regenerate the SDK"}
    fresh = current == locked and client_current == client_locked
    return {"name": "sdk-freshness", "ok": fresh, "blocking": True,
            "code": "sdk_fresh" if fresh else "sdk_stale",
            "detail": "SDK matches the current OpenAPI contract" if fresh else "SDK contract lock is stale",
            "remediation": "none" if fresh else "Run smartvintaawesomekit sdk generate --project ."}


@sdk_app.command("check")
def check(
    project: Annotated[Path, typer.Option("--project")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json")] = False,
    language: Annotated[str, typer.Option("--language")] = "typescript",
) -> None:
    """Fail when the generated SDK does not match the current OpenAPI contract."""
    project = project.resolve()
    client_path, _contract_path, lock_path = _paths(project, language)
    try:
        current = hashlib.sha256(_canonical(_contract(project))).hexdigest()
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        locked = lock.get("openapi_sha256")
        client_current = hashlib.sha256(client_path.read_bytes()).hexdigest()
        client_locked = lock.get("client_sha256")
    except (RuntimeError, OSError, json.JSONDecodeError):
        current, locked, client_current, client_locked = "unavailable", None, None, None
    fresh = current == locked and client_current == client_locked and locked is not None
    payload = {"status": "fresh" if fresh else "stale", "openapi_sha256": current,
               "locked_sha256": locked,
               "remediation": "none" if fresh else "Run smartvintaawesomekit sdk generate --project ."}
    typer.echo(json.dumps(payload, indent=2) if json_output else f"SDK contract: {payload['status']}")
    if not fresh:
        raise typer.Exit(1)


__all__ = ["check", "freshness", "generate", "sdk_app"]
