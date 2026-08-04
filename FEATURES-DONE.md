## Features Done (v0.9.10 fix pass)
- clean-checkout pytest plugin subprocesses use the active Python interpreter and preserve the active import environment
- canonical CLI implementation lives in `cli/core.py`; legacy `cli.py` is a compatibility shim; `python -m smartvintaawesomekit.cli` is supported
- `pytest-cov` is declared in development and test extras
- unexplained nested generated project artifact removed
- capability claims separated into shipped, partial, and roadmap scope in `CAPABILITY-MATRIX.md`
- independent QA findings retained with remediation status
- full regression suite passes: 1,061 passed, 0 failed

## Previously shipped and verified
- persistent SQLite CRUD resource generation for primitive fields
- Alembic upgrade/downgrade/current/history wrappers
- persisted refresh-token rotation and reuse detection primitives
- SQLite/app-import/SDK readiness checks
- managed-file conflict-blocking upgrade apply
- Redis namespace safety
- deterministic schema-aware TypeScript and Python SDKs

## Explicit non-claims
- full SaaS auth route vertical slice is roadmap, not shipped
- resource relationships, operation selection, and rich constraints are roadmap
- complete migration drift/head policy is roadmap
- full PostgreSQL/Redis/CVE/worker/email readiness is roadmap
- P3 business and organization policy packs are roadmap

## Sources
- `research-findings.md` priority list
- `CAPABILITY-MATRIX.md` authoritative scope
- `review-findings.md` independent audit and remediation appendix
- `CHANGELOG.md` v0.9.10 section
