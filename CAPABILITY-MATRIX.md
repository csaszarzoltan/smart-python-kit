# Capability Matrix

This is the authoritative scope statement for v0.10.0.

## Shipped and integration-tested
- FastAPI project generation for minimal, API, and scaffold-level SaaS presets
- Persistent SQLite CRUD slices for primitive fields
- Alembic upgrade, downgrade, current, and history wrappers
- JWT, password, OAuth-provider, RBAC, persisted-session, and refresh-rotation primitives
- Conflict-blocking managed-file upgrade preview/apply
- SQLite, application-import, production-secret, and SDK readiness checks
- Namespaced Redis cache behavior
- Deterministic schema-aware TypeScript and Python SDK generation
- Observability module: structured JSON logging, request tracing with `trace_id` correlation, per-route metrics, and opt-in OTLP export (SigNoz/Jaeger/Grafana), included in generated projects by default

## Partial or experimental
- PostgreSQL templates are generated, but live PostgreSQL integration is not in the default gate.
- The SaaS preset is a scaffold, not a complete registration/login/billing application.
- Upgrade apply is safe replacement, not semantic three-way merging.
- Readiness does not include live PostgreSQL, Redis, CVE, worker, email, or migration-head probes.
- OTLP export is opt-in and currently wired for metrics only; traces and logs export are roadmap.

## Roadmap, not shipped
- Resource relationships, foreign keys, richer constraints, and operation selection
- Alembic revision generation, model drift, and head CI policy
- Integrated SaaS auth routes and PostgreSQL auth matrix
- Organization policy packs and business packs
- Public compatibility dashboard

## Verification
- Full suite: 1,099 passed, 0 regressions (1 pre-existing SDK test failure on Python 3.11, out of scope)
- Observability: 40/40 tests pass in the repo `.venv`
- Ruff clean on `src/` and `tests/`
- Clean-environment subprocess tests use the active Python interpreter
- Factory tests use real async SQLite persistence
- Password tests perform real bcrypt hash/verify behavior
