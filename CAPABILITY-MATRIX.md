# Capability Matrix

This file is the authoritative statement of shipped scope for v0.9.10. Research priorities not listed as shipped remain roadmap items.

## Shipped and integration-tested
- FastAPI project generation for minimal, API, and scaffold-level SaaS presets
- SQLite persistent CRUD resource slices for primitive fields
- Alembic upgrade, downgrade, current, and history command wrappers
- JWT, password, OAuth-provider, RBAC, persisted-session, and refresh-rotation primitives
- Managed-file upgrade preview/apply with drift blocking and manifest backup
- SQLite connectivity, application import, production-secret, and SDK freshness readiness checks
- Namespaced Redis cache behavior
- Deterministic schema-aware TypeScript and Python SDK generation and freshness checks

## Explicitly experimental or partial
- PostgreSQL project templates are generated, but live PostgreSQL integration is not part of the default test gate.
- The `saas` preset is a scaffold preset. It does not ship registration, login, verification, reset, billing, email, teams, or admin routes.
- Managed-file apply is conflict-blocking replacement, not a semantic three-way merge.
- Readiness does not yet include live PostgreSQL, Redis, CVE, worker, email, or migration-head probes.

## Roadmap, not shipped
- Resource relationship/foreign-key generation, uniqueness constraints, and operation selection
- Alembic revision generation, model-drift comparison, and migration-head CI policy
- Integrated SaaS auth route journey and PostgreSQL auth matrix
- Organization policy packs and constrained custom presets
- Stripe, teams/invitations, email workflow, audit, admin UI, and background-job packs
- Public compatibility dashboard
