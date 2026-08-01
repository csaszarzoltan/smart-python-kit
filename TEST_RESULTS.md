# Test results

## Environment

- Validation date: 2026-08-01
- Python: 3.12 in the execution container
- Source package version: 0.4.0

## Targeted product-experience tests

Command:

```bash
PYTHONPATH=/opt/oai-pkgs:src pytest -q tests/test_cli.py tests/test_cli_product_experience.py
```

Result: **14 passed**.

Covered behavior:

- dry-run makes no file-system changes,
- API preset generates guidance, configuration, example route, and tests,
- non-empty destinations are not overwritten,
- invalid/path-like names are rejected,
- PostgreSQL selection changes dependencies and URL,
- doctor returns successful machine-readable diagnostics,
- current legacy CLI interface checks remain green.

## Generated-project acceptance tests

An API-preset project was generated into a clean temporary directory and its own tests were run with third-party pytest plugin autoload disabled to isolate the generated application.

Result: **4 passed**.

Covered behavior:

- health endpoint,
- root navigation guidance,
- create/get item journey,
- invalid item form validation.

## Full regression suite

Result: **800 passed, 11 failed, 10 warnings**.

The same 11 failure categories were present in the supplied baseline before this implementation. They are environment/dependency or pre-existing module concerns involving bcrypt/passlib compatibility, Redis test setup, and subprocess pytest-plugin discovery. The changed CLI introduced no remaining regression. Detailed console output is stored in `test-results/full-regression.txt`.

## Static validation

- `py_compile` passed for modified Python modules.
- Ruff could not be executed because the binary was not available in the execution environment.
