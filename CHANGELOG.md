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
