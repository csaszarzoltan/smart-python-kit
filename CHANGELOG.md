# Changelog

## v0.9.4 - 2026-08-04

### Features
- Added mandatory Redis application/environment namespaces to every cache key operation.
- Added cursor-based namespace clearing that deletes only matching keys in bounded batches.
- Added namespace support to both direct construction and `RedisCache.from_url()`.

### Security
- Removed `flushdb()` from normal cache clearing so shared Redis databases cannot lose unrelated application data.
- Reject empty, whitespace-padded, and wildcard namespaces before connecting or writing.

### Tests
- Added TDD coverage for namespaced get/set/exists/delete, isolated clearing, multi-batch scans, and invalid namespaces.

### Docs
- Updated Redis examples, safety guidance, and the machine-readable feature manifest.

## v0.9.3 - 2026-08-04

### Features
- Added `upgrade-apply` with read-only preview and JSON output for safe current-template upgrades.
- Added whole-project conflict classification for modified, missing, and unmanaged target paths.
- Added staged managed-file replacement, pre-apply manifest backup, and refreshed checksums/baselines.

### Safety
- Upgrades refuse to write when any managed file has drifted or a template target collides with an unmanaged path.
- Resource-generated and user-authored files outside the current template remain untouched.

### Tests
- Added TDD acceptance coverage for dry-run, successful application, manifest refresh, backup creation, conflicts, no-partial-write behavior, and unknown schemas.

### Docs
- Documented the plan-preview-apply workflow and updated the feature manifest.

## v0.9.2 - 2026-08-04

### Features
- Added opt-in `doctor --connectivity` SQLite connectivity checks using a non-destructive `SELECT 1` probe.
- Added opt-in `doctor --startup` ASGI import verification in an isolated, time-bounded subprocess.
- Added stable readiness codes, durations, blocking status, and actionable remediation to JSON diagnostics.

### Security
- Readiness failures suppress internal exception text and never emit environment values or credentials.

### Tests
- Added TDD acceptance coverage for successful real I/O, unsupported URLs, import failures, redaction, and opt-in behavior.

### Docs
- Documented evidence-based readiness checks and updated the feature manifest.

## v0.9.1 - 2026-08-04

### Features
- Added persisted refresh-token rotation that validates active sessions, revokes used JTIs, creates replacement sessions, and preserves client metadata.

### Security
- Reject reused, revoked, missing, expired, and access-token inputs during refresh rotation.

### Tests
- Added real async SQLite integration coverage for rotation, reuse detection, expiry, and token-type validation.

### Docs
- Documented the production session-rotation API and updated the machine-readable feature manifest.

## v0.9.0 - 2026-08-04

### Features
- Added persistent vertical-slice generation for SQLAlchemy models, Pydantic schemas, async services, full CRUD routes, Alembic revisions, and integration tests.
- Added safe `migrate` preview/execution for Alembic upgrade, downgrade, current, and history operations.
- Consolidated the installed command surface under the canonical `smartvintaawesomekit.cli.core` application.

### Fixes
- Reject duplicate and reserved resource fields before any project files are written.
- Track every generated persistent-resource file and updated router registration in the scaffold manifest.

### Tests
- Added TDD acceptance, validation, command-safety, and real SQLite CRUD integration coverage.

### Docs
- Updated README workflows and added `FEATURES-DONE.md` for machine-readable release discovery.

### v0.8.0 — Upgrade planning and shared quality gates (2026-08-01)

#### Added
- Read-only `upgrade-plan` with conflict classification and CI check mode
- Previewable `manifest-repair` with backups and schema protection
- Generated GitHub Actions quality workflow
- Generated local `scripts/check.py` quality gate
- v0.8 release and validation reports

#### Changed
- New CI and quality files participate in managed-file tracking
- README and package version updated

### v0.7.0 — Actionable drift lifecycle (2026-08-01)

#### Added
- Versioned manifest schema with managed text baselines
- Safe `inspect --diff` output in human and JSON modes
- Previewable `manifest-accept` with backups and sensitive-file protection
- Optional Redis and Alembic capability diagnostics
- v0.7 product, UX, release, and validation reports

#### Changed
- Resource generation records v1 managed-file metadata
- README and package version updated

### v0.6.0 — Drift visibility and stable API errors (2026-08-01)

#### Added
- Checksum-aware scaffold manifest and resource metadata
- Read-only `inspect` command with JSON and CI check modes
- Stable API error envelope with field validation details and request IDs
- Production JWT secret validation in `doctor`
- v0.6 release and validation reports

#### Changed
- Resource generation updates managed-file checksums
- Exception handling preserves legacy mapping keys while registering typed FastAPI handlers
- README and package version updated

### v0.5.0 — Workflow extension and production readiness (2026-08-01)

#### Added
- Safe `add-resource` generator with field validation, preview, JSON output, tests, and conflict protection
- Alembic migration scaffolding in generated projects
- Request-ID middleware scaffolding
- Production-aware doctor checks
- v0.5 requirements, implementation, and validation report

#### Changed
- Pagination now validates bounds and applies limit/offset
- Generated projects include migration and traceability foundations
- README and package version updated

### v0.5.0-next — User-centered generator workflow (2026-08-01)

#### Added
- Preset-based generation (`minimal`, `api`, `saas`)
- Dry-run and JSON output
- Atomic generation and overwrite protection
- Project-name, preset, and database validation
- SQLite/PostgreSQL-specific output
- `.env.example` and scaffold manifest
- `doctor` diagnostics
- Example API vertical slice with acceptance tests
- Product/UX and implementation reports

#### Changed
- Generated projects now contain health/navigation guidance and current setup documentation
- Demo application version derives from the package version
- README documents the user-centered workflow

# Changelog

All notable changes to this project will be documented in this file.

## v0.4.0 — Testing Module (2026-07-27)

### Added
- New `smartvintaawesomekit.testing` package with:
  - **Factories** — ModelFactory base class with UserFactory, RoleFactory, SessionRecordFactory, UserRoleFactory (build/create patterns, field overrides)
  - **Database Fixtures** — In-memory SQLite async fixtures (db_engine, db_session) for isolated test databases
  - **Client Fixtures** — async_client FastAPI TestClient with auth header helpers
  - **Mock Registry** — Pre-built mocks for auth (MockJWTManager, MockPasswordHasher, MockRBACManager, MockAuthConfig), cache (MockCacheBackend), HTTP (MockAsyncClient), and database (MockAsyncSession, MockCRUD)
  - **Pytest Plugin** — Auto-registers all fixtures via pytest11 entry point, no manual conftest.py required
  - **Helpers** — assert_response, assert_paginated, auth_header utilities
- Optional [test] extra already covers required deps (pytest, pytest-asyncio, httpx)

### Tests
- 393+ tests covering the testing module itself (factories, mocks, fixtures, plugin)
- >= 85% code coverage on smartvintaawesomekit.testing
- Zero regressions on existing 400+ tests

### Dependencies
- No new runtime dependencies added
- All mocking uses stdlib unittest.mock

## v0.3.0 — Caching Module (2026-07-25)

### Added
- Cache module with 7 sub-modules:
  - `cache/base.py` — Abstract `CacheBackend` interface (get, set, delete, exists, clear, get_stats)
  - `cache/config.py` — `CacheConfig` with `CACHE_*` environment variable support
  - `cache/memory.py` — Thread-safe in-memory cache with TTL and LRU eviction
  - `cache/redis.py` — Async Redis backend via `redis.asyncio` (optional `[redis]` extra)
  - `cache/decorator.py` — `@cached()` decorator for sync/async functions and FastAPI routes
  - `cache/invalidation.py` — Tag-based and prefix-based cache invalidation
  - `cache/stats.py` — `CacheStats` dataclass with hit rate tracking
- Optional `[redis]` dependency for Redis backend
- 131 tests covering all cache sub-modules
- Documentation in `docs/caching.md` and `examples/caching_example.py`

## v0.2.0 — 2026-07-25

Full authentication module — JWT, OAuth2, RBAC, password hashing, session management, and middleware.

### Features
- **Authentication module** (`smartvintaawesomekit.auth`) — complete auth system with 7 sub-modules:
  - **JWT** — Access/refresh token creation, decoding, validation, and refresh pairing (PyJWT, HS256)
  - **OAuth2** — Authorization code flow for Google and GitHub providers with CSRF state protection
  - **RBAC** — Role-based access control with hierarchical roles and decorator-based route protection
  - **Password hashing** — Algorithm-agnostic hasher (bcrypt/argon2) via passlib with timing-safe verification
  - **Session management** — Server-side refresh token tracking with revocation support (SQLAlchemy)
  - **Middleware** — FastAPI middleware that validates JWT and injects user into `request.state`
  - **Config** — Pydantic-settings `AuthConfig` loaded from `AUTH_*` environment variables
- **Auth ORM models** — `User`, `Role`, `UserRole`, `SessionRecord` with indexed columns and FK relationships
- **Auth dependencies** — `create_auth_dependencies()` factory for pre-configured FastAPI DI wiring

### Dependencies
- Added `PyJWT>=2.8.0`, `passlib[bcrypt]>=1.7.4`, `argon2-cffi>=23.1.0`

### Tests
- 176 auth tests across 9 test classes (153 interface + 23 behavioral)
- 281 total tests (105 existing + 176 auth), zero regressions
- Ruff clean on `src/`

### Security
- JWT refresh tokens properly validate (reject expired/tampered tokens)
- `decode_token` propagates `JWTError` instead of swallowing exceptions
- OAuth2 HTTP requests use 10-second timeout
- RBACManager uses module-level singleton (no per-request instantiation)
- Middleware logs specific JWT error types instead of silent catch-all
- No secrets in logs or error messages

## v0.1.0 — 2026-07-22

Initial MVP release of smartvintaawesomekit — a Smart Python developer toolkit.

### Features
- **Configuration management** — Pydantic V2 settings with environment variable loading, field descriptions, and `__all__` exports
- **Async SQLAlchemy 2.0 database** — Async session factory with `get_session()` generator, CRUD base class with create/read/update/delete operations, and graceful handling of `db=None` for smoke tests
- **FastAPI API layer** — Health check endpoint, generic request/response models, three exception handlers (validation, not-found, generic), and a `create_app()` factory
- **Typer CLI application** — Server management (start with configurable host/port/reload), version display, and `isinstance` guard for direct callback invocation
- **Packaging** — PEP 621 compliant `pyproject.toml` with `smartvintaawesomekit` CLI entry point
- **Railway deployment** — `railway.toml` with Railpack builder, ASGI entry point (`app.py`) with health endpoint and exception handlers
- **Example project** — `test-project/` directory demonstrating the output of the CLI `init` command

### Tests
- 105 tests total (91 interface + 14 behavioral) across 4 test modules
- `test_config.py` — 39 tests covering field presence, types, defaults, env loading, and optional config
- `test_database.py` — 29 tests covering session lifecycle, CRUD operations, and error handling
- `test_api.py` — 29 tests covering health endpoint, exception handlers, response models, and app factory
- `test_cli.py` — 8 tests covering CLI commands, flags, and version output
- Ruff linting clean (0 errors, 0 warnings)
