# Independent QA Review and Remediation Record

## Original v0.9.9 verdict

**REJECTED.** The audit found a non-reproducible test gate, `.venv` and system-Python assumptions, duplicated CLI implementation, un-awaited factory pseudo-tests, focused-only coverage claims, an unexplained nested generated project, stale placeholder-era tests, and overstated roadmap completion.

## Remediation through v0.9.12

- Subprocess tests use `sys.executable` and preserve the active environment.
- Generated-resource integration no longer hardcodes `/usr/bin/python3` or `/opt/oai-pkgs`.
- The legacy CLI module is a compatibility shim; module execution works.
- Factory persistence tests use real async SQLite rows.
- Password and Redis tests verify real behavior.
- Bcrypt, Redis, and coverage test dependencies are pinned/declared.
- Placeholder-era and RED-phase wording was removed without hiding roadmap gaps.
- Whole-package coverage is measured rather than inferred from focused suites.
- Documentation distinguishes shipped, partial, and roadmap capabilities.

## Current verdict

**APPROVED WITH NOTES as a foundation release.** Release integrity issues are corrected. Product capabilities listed as roadmap in `CAPABILITY-MATRIX.md` are not claimed as shipped.

## Evidence
- 1,060 passed, 0 failed, 0 warnings
- 84% whole-package statement coverage across 2,407 statements
- repository Ruff gate passed
- Python compilation passed
