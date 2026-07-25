# SmartVintaAwesomeKit

Smart Python developer toolkit — batteries-included project generator, configuration management, database utilities, API helpers, and a complete authentication module for modern Python applications.

## Quick Start

```bash
# Install
pip install smartvintaawesomekit

# Create a new project
smartvintaawesomekit init my-project
cd my-project

# Run the generated app
uvicorn app.main:app --reload
```

## Features

- **Smart Configuration** — pydantic-settings with sensible defaults
- **Smart Database** — Async SQLAlchemy session management + CRUD helpers
- **Smart API** — Standardized response formats, pagination, error handling
- **Smart CLI** — Project generator that scaffolds FastAPI apps in seconds
- **Authentication** — JWT tokens, OAuth2 (Google/GitHub), RBAC, password hashing, session management
- **Testing Helpers** (P1) — Fixtures and utilities for testing FastAPI apps
- **Deployment Templates** (P1) — Railway-ready Dockerfile and configuration

## Authentication

Complete auth system with 7 sub-modules. Requires environment variables prefixed with `AUTH_`:

```bash
export AUTH_JWT_SECRET_KEY="your-secret-key-at-least-32-bytes-long"
```

### Setup

```python
from fastapi import FastAPI
from smartvintaawesomekit.auth import AuthConfig, create_auth_dependencies

app = FastAPI()
config = AuthConfig()
deps = create_auth_dependencies(config)

# Add JWT middleware (validates Bearer tokens, sets request.state.user)
app.add_middleware(deps["middleware"], skip_paths=["/health", "/docs"])

# Protected route
@app.get("/me")
async def me(user=deps["get_current_user"]):
    return {"user_id": user["sub"]}
```

### Auth sub-modules

| Module | Purpose |
|--------|---------|
| `auth.jwt` | Access/refresh token creation, decoding, validation |
| `auth.password` | Password hashing (bcrypt/argon2) via passlib |
| `auth.oauth2` | Google and GitHub OAuth2 authorization code flow |
| `auth.rbac` | Role-based access control with `@require_role` / `@require_permission` decorators |
| `auth.session` | Server-side refresh token tracking and revocation |
| `auth.middleware` | FastAPI middleware for JWT validation + user injection |
| `auth.config` | Pydantic-settings `AuthConfig` loaded from `AUTH_*` env vars |

See [docs/auth.md](docs/auth.md) for the full usage guide.

## Development

```bash
# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check .

# Type check
mypy src/
```

## License

MIT
