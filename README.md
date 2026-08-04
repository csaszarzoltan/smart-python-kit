# SmartVintaAwesomeKit

SmartVintaAwesomeKit is a batteries-included Python toolkit for creating and extending FastAPI applications. It combines safe project scaffolding, validated configuration, async SQLAlchemy utilities, API helpers, authentication, caching, testing utilities, and deployment-ready project files.

**Current version:** 0.9.12  
**Project status:** Alpha

> The v0.5 release focuses on safer repeated developer workflows: previewable project generation, resource generation, migration scaffolding, request tracing, bounded pagination, and production-oriented diagnostics.

## Highlights in v0.6

- Preset-based project generation: `minimal`, `api`, and `saas`
- Atomic file generation with overwrite protection
- `--dry-run` previews and `--json` automation output
- SQLite and PostgreSQL-specific generated configuration
- Safe `add-resource` workflow with typed fields and generated tests
- Alembic migration scaffolding in generated projects
- `X-Request-ID` middleware scaffolding for request correlation
- Pagination validation with SQL limit and offset application
- Production-aware `doctor` diagnostics
- Updated generated README, environment template, and scaffold manifest

See the [v0.5 release report](docs/v0.5-release-report.md), [implementation report](docs/implementation-report.md), and [product and UX requirements](docs/product-ux-requirements-report.md) for the full analysis and rationale.

## Capability status

v0.9.12 is a verified foundation release, not completion of the entire research roadmap. See [`CAPABILITY-MATRIX.md`](CAPABILITY-MATRIX.md) for shipped, partial, and roadmap scope.

The clean development environment reports **1,060 passed, 0 failed, 0 warnings** and **84% whole-package statement coverage**.

## Installation

```bash
pip install smartvintaawesomekit
```

For local development:

```bash
git clone <repository-url>
cd smartvintaawesomekit
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,test]"
```

## Quick start

### 1. Preview generation

```bash
smartvintaawesomekit init my-api   --preset api   --database sqlite   --dry-run
```

The preview lists the files that would be created without modifying the file system.

### 2. Generate the project

```bash
smartvintaawesomekit init my-api   --preset api   --database sqlite

cd my-api
cp .env.example .env
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> after starting the server.

### 3. Validate the project

```bash
smartvintaawesomekit doctor --project .
```

For production-oriented checks:

```bash
smartvintaawesomekit doctor   --project .   --environment production
```

Use `--json` with generation, diagnostics, and resource workflows when integrating the CLI into scripts or CI.

### Drift inspection and CI checks

```bash
# Human-readable provenance and drift report
smartvintaawesomekit inspect --project .

# Fail CI when generator-managed files are missing or modified
smartvintaawesomekit inspect --project . --check --json
```

The scaffold manifest now stores SHA-256 hashes for generator-managed files and resource metadata. `inspect` is read-only and reports missing or modified managed files without overwriting developer changes.

### Stable API error contract

Registered FastAPI exception handlers now return a consistent envelope with a stable error code, user-facing message, field-level validation details, and request ID. Responses also include `X-Request-ID` for log correlation.

```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid",
    "fields": [{"field": "body.name", "message": "Field required"}],
    "request_id": "..."
  }
}
```

### Stronger production diagnostics

Production `doctor` checks now detect absent or placeholder JWT secrets. `AUTH_JWT_SECRET_KEY` must contain a non-placeholder value of at least 32 characters. Secret values are never printed.

## v0.7 lifecycle workflows

### Explain managed-file drift

```bash
smartvintaawesomekit inspect --project . --diff
smartvintaawesomekit inspect --project . --diff --json
```

New projects use manifest schema version 1. For each generator-managed text file, the manifest stores a SHA-256 checksum and a Base64-encoded generated baseline. `inspect --diff` compares that baseline with the current file and produces a unified diff without changing the project.

### Accept an intentional managed-file change

Preview acceptance first:

```bash
smartvintaawesomekit manifest-accept app/main.py \
  --project . \
  --dry-run \
  --json
```

Apply the selected acceptance:

```bash
smartvintaawesomekit manifest-accept app/main.py --project .
```

Only explicitly selected, generator-managed UTF-8 text files can be accepted. Environment and secret-like paths are rejected. Before changing the manifest, the command writes `.smartvinta.json.bak`.

### Optional capability diagnostics

`doctor` now reports whether Redis and Alembic support are installed. Missing optional capabilities are shown with installation guidance but do not block unrelated core workflows. Production security checks remain blocking.

## v0.8 upgrade and quality workflows

### Plan an upgrade safely

```bash
smartvintaawesomekit upgrade-plan --project .
smartvintaawesomekit upgrade-plan --project . --check --json
```

The command is read-only. It compares the project manifest version with the installed toolkit and classifies the project as `current`, `upgrade_available`, or `conflicts`. Modified or missing managed files are listed as manual actions rather than overwritten.

### Repair supported manifest metadata

```bash
smartvintaawesomekit manifest-repair --project . --dry-run --json
smartvintaawesomekit manifest-repair --project .
```

Repair is intentionally narrow. It restores supported metadata such as schema version 1 and invalid resource containers, creates `.smartvinta.json.bak`, and refuses unknown newer schemas or invalid JSON. It does not accept file drift.

### Use the same quality gate locally and in CI

Generated projects now include:

```text
.github/workflows/quality.yml
scripts/check.py
```

Run the local gate with:

```bash
python scripts/check.py
```

The generated GitHub Actions workflow invokes the same script so local and CI behavior stay aligned.

## Project presets

### `minimal`

Generates the smallest supported FastAPI project with configuration, database setup, health endpoint, tests, environment template, Dockerfile, scaffold manifest, migration foundation, and request-ID middleware.

### `api`

Includes the minimal foundation plus a documented example API vertical slice and its acceptance tests. This is the recommended starting point for most services.

### `saas`

Uses the expanded project structure intended for applications that will adopt authentication, sessions, caching, and role-based permissions. The toolkit contains these modules, but fully generated database-backed authentication composition remains a planned follow-up.

## Safe project generation

```bash
# SQLite
smartvintaawesomekit init service-name   --preset api   --database sqlite

# PostgreSQL
smartvintaawesomekit init service-name   --preset api   --database postgresql
```

Generation behavior:

- project names are validated before files are written,
- output is staged before it is moved into the destination,
- non-empty destinations are not overwritten silently,
- `--force` must be supplied explicitly to replace a destination,
- `.env.example` documents generated configuration,
- `.smartvinta.json` records the generator version, preset, and database choice.

## Add an API resource

Preview the change first:

```bash
smartvintaawesomekit add-resource product   --project .   --field name:str:required   --field price:float:required   --field description:str:optional   --dry-run
```

Apply the resource:

```bash
smartvintaawesomekit add-resource product   --project .   --field name:str:required   --field price:float:required   --field description:str:optional
```

The command:

- validates the resource and field specifications,
- refuses to overwrite an existing resource,
- creates a route module,
- creates an API journey test,
- registers the router in `app/main.py`,
- supports JSON output for automation.

Supported field types in v0.5 are `str`, `int`, `float`, and `bool`. Each field must be marked `required` or `optional`.

> Resource generation currently creates an in-memory API vertical slice. SQLAlchemy model creation, persistence services, and automatic Alembic revisions are intentionally deferred to a later release.

## Migrations

Generated projects include an Alembic-compatible starting structure:

```text
alembic.ini
migrations/
├── env.py
├── script.py.mako
└── versions/
```

The v0.5 release establishes the migration layout and project contract. Before production use, connect the generated project’s model metadata and create application-specific revisions.

## Request tracing

Generated projects include request-ID middleware. The middleware:

- preserves an incoming `X-Request-ID`,
- generates a UUID when the header is absent,
- stores the ID on `request.state`,
- returns the ID in the response header.

This provides a foundation for structured logging and support diagnostics.

## Pagination

The `paginate()` helper now validates inputs and applies SQL pagination:

```python
from sqlalchemy import select
from smartvintaawesomekit.api import paginate

query, page, size = paginate(select(MyModel), page=2, size=25)
```

Rules:

- `page` must be at least 1,
- `size` must be between 1 and 100,
- offset is calculated as `(page - 1) * size`,
- the returned SQLAlchemy query contains the corresponding limit and offset.

## Main toolkit modules

- **Configuration:** Pydantic Settings-based application, API, database, CORS, auth, and cache configuration
- **Database:** async SQLAlchemy sessions and generic CRUD utilities
- **API:** response models, error handlers, and pagination
- **Authentication:** JWT, password hashing, OAuth2 providers, RBAC, session tracking, and FastAPI dependencies
- **Caching:** in-memory and optional Redis backends, decorators, invalidation, and statistics
- **Testing:** async client and database fixtures, factories, mocks, and response assertions
- **CLI:** project generation, diagnostics, version output, and incremental resource generation

## Authentication

Authentication uses environment variables prefixed with `AUTH_`:

```bash
export AUTH_JWT_SECRET_KEY="replace-with-a-secret-of-at-least-32-bytes"
```

Example setup:

```python
from fastapi import FastAPI
from smartvintaawesomekit.auth import AuthConfig, create_auth_dependencies

app = FastAPI()
config = AuthConfig()
deps = create_auth_dependencies(config)

# Wire the returned dependencies according to the application integration pattern.
@app.get("/me")
async def me(user=deps["get_current_user"]):
    return {"user_id": user["sub"]}
```

Authentication capabilities include:

- access and refresh JWT creation and validation,
- bcrypt or Argon2 password hashing,
- Google and GitHub OAuth2 provider abstractions,
- role and permission checks,
- refresh-session persistence and revocation primitives,
- FastAPI authentication dependencies and middleware.

See [Authentication documentation](docs/auth.md) for details.

## Caching

The cache package provides:

- thread-safe in-memory caching,
- optional Redis support,
- TTL and LRU behavior,
- sync and async caching decorators,
- tag and prefix invalidation,
- cache statistics.

See [Caching documentation](docs/caching.md) for configuration and examples.

## Development and validation

```bash
# Run the full test suite
pytest -q

# Run the v0.5 focused tests
pytest -q   tests/test_cli.py   tests/test_cli_product_experience.py   tests/test_next_release.py

# Lint
ruff check .

# Type check
mypy src/

# Compile-check modified modules
python -m py_compile src/smartvintaawesomekit/*.py
```

Validation recorded for the packaged v0.5 handoff:

- 69 targeted API, CLI, and release tests passed,
- 5 clean generated-project acceptance tests passed after adding a resource,
- the full suite completed with 814 passing tests,
- 11 existing environment or baseline failures remain documented,
- the final ZIP passed archive integrity validation.

See [v0.5 test results](TEST_RESULTS_V0.5.md) and the detailed output under `test-results/`.

## v0.6 validation summary

- 6 new TDD acceptance tests passed.
- 69 targeted API, CLI, and release tests passed.
- 5 clean generated-project acceptance tests passed.
- Full regression result: 825 passed, 11 pre-existing environment/baseline failures, and 11 warnings.

See [v0.6 test results](TEST_RESULTS_V0.6.md) and [v0.6 release report](docs/v0.6-release-report.md).

## Known limitations

- The project is still classified as Alpha.
- The generated migration structure is a foundation, not a complete model-autogeneration workflow.
- `add-resource` currently generates an in-memory vertical slice rather than database persistence.
- Fully composed database-backed registration, login, token rotation, and logout are not yet generated by the `saas` preset.
- Existing environment-sensitive test failures involving Passlib/bcrypt, Redis setup, and subprocess pytest plugin discovery are documented in the packaged test results.

## Documentation

- [Authentication guide](docs/auth.md)
- [Caching guide](docs/caching.md)
- [Product and UX requirements](docs/product-ux-requirements-report.md)
- [Implementation report](docs/implementation-report.md)
- [v0.5 release report](docs/v0.5-release-report.md)
- [Test results](TEST_RESULTS_V0.5.md)
- [Changelog](CHANGELOG.md)

## License

MIT
