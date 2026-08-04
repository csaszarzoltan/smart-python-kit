## Features Done (this pass)
- canonical CLI package: routes the installed entry point through one lifecycle CLI while preserving helper-module imports
- persistent vertical-slice generator: creates SQLAlchemy model, Pydantic schemas, async service, full CRUD router, Alembic revision, and integration tests
- resource validation: rejects duplicate, reserved, malformed, and unsupported fields before writing
- managed resource lifecycle: records all generated files and router updates in the versioned scaffold manifest
- operational migration command: safely previews or runs Alembic upgrade, downgrade, current, and history operations
- generated SQLite integration flow: verifies create, list, read, partial update, delete, validation, and not-found behavior with real I/O
- persisted refresh-token rotation: validates active database sessions, revokes used tokens, creates replacement sessions, and rejects reuse or expiry
- evidence-based readiness gate: performs opt-in real SQLite connectivity and isolated ASGI import checks with stable codes, timings, redaction, and remediation
## Sources
- research-findings.md items addressed: P0 canonical green CLI foundation, P1 persistent add-resource, P1 complete migration lifecycle foundation, P1 integrated production auth/session composition, P2 expand doctor into readiness policy
- CHANGELOG.md section this maps to: v0.9.2, v0.9.1, and v0.9.0 sections - 2026-08-04
