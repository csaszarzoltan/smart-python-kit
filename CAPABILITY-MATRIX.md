# Capability Matrix

This is the authoritative scope statement for v0.9.12.

## Shipped and integration-tested
- FastAPI project generation for minimal, API, and scaffold-level SaaS presets
- Persistent SQLite CRUD slices for primitive fields
- Alembic upgrade, downgrade, current, and history wrappers
- JWT, password, OAuth-provider, RBAC, persisted-session, and refresh-rotation primitives
- Conflict-blocking managed-file upgrade preview/apply
- SQLite, application-import, production-secret, and SDK readiness checks
- Namespaced Redis cache behavior
- Deterministic schema-aware TypeScript and Python SDK generation

## Partial or experimental
- PostgreSQL templates are generated, but live PostgreSQL integration is not in the default gate.
- The SaaS preset is a scaffold, not a complete registration/login/billing application.
- Upgrade apply is safe replacement, not semantic three-way merging.
- Readiness does not include live PostgreSQL, Redis, CVE, worker, email, or migration-head probes.

## Roadmap, not shipped
- Resource relationships, foreign keys, richer constraints, and operation selection
- Alembic revision generation, model drift, and head CI policy
- Integrated SaaS auth routes and PostgreSQL auth matrix
- Organization policy packs and business packs
- Public compatibility dashboard

## Verification
- Full suite: 1,060 passed, 0 failed, 0 warnings
- Whole-package statement coverage: 84%
- Clean-environment subprocess tests use the active Python interpreter
- Factory tests use real async SQLite persistence
- Password tests perform real bcrypt hash/verify behavior
