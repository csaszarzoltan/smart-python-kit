# Release Verification

## Release
- Version: 0.9.10
- Verification date: 2026-08-04
- Product surface: Python library and CLI; generated FastAPI APIs expose OpenAPI `/docs`; no standalone web UI is applicable

## Required Gates
- Setup command: `python -m pip install -e ".[dev]"`
- Full regression command: `pytest -q`
- Repository lint command: `ruff check .`
- Python compilation command: `python -m compileall -q src tests`
- Archive validation command: `unzip -t SmartVintaAwesomeKit-v0.9.9.zip`

## Verified Results
- Full regression: 1,061 passed, 0 failed, 12 non-blocking warnings
- Repository lint: 0 errors across the complete repository
- SDK focused coverage: 93% across TypeScript, Python, lock, tamper, and readiness paths
- Pre-release integrity baseline: every pre-existing file present; no silent deletions
- Packaging exclusions: `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.coverage`, `*.pyc`, and `*.db` excluded
- ZIP structure: validated with no compressed-data errors

## Scoped Ruff Compatibility Policy
The repository keeps explicit per-path exceptions for historical tests, examples, the legacy `src/smartvintaawesomekit/cli.py` compatibility module, and deliberately dynamic API/cache signatures. These exceptions are configuration-visible rather than hidden inline. Current feature modules including `cli/core.py`, `resource_cli.py`, `readiness.py`, `sdk.py`, auth session rotation, and new release tests are linted under their declared strict scopes.

## Remaining Non-Blocking Warnings
- Third-party Starlette TestClient deprecation notice
- Intentionally short JWT secrets in legacy negative tests
- Non-interactive password prompt warning in a legacy CLI test
- Legacy factory tests that invoke async methods synchronously

These warnings do not fail the suite. They are preserved as historical compatibility behavior and are not represented as production readiness failures.

## v0.9.10 Independent QA Remediation
- Removed all test assumptions about a repository-local `.venv`.
- Re-ran the full suite with the active installed environment: 1,061 passed, 0 failed.
- Added `CAPABILITY-MATRIX.md`; incomplete research priorities are now explicitly roadmap, not release claims.
- Replaced duplicated `cli.py` implementation with a compatibility shim and added module execution.
