# Authentication Module

Complete authentication system for FastAPI applications — JWT tokens, OAuth2 login, role-based access control, password hashing, session tracking, and middleware integration.

## Installation

The auth module is included in `smartvintaawesomekit`. Install with optional auth dependencies:

```bash
pip install smartvintaawesomekit
```

Core auth dependencies (installed automatically):
- `PyJWT` — JWT encoding/decoding
- `passlib[bcrypt]` — password hashing
- `argon2-cffi` — alternative password hashing
- `httpx` — OAuth2 HTTP calls

## Configuration

All auth settings are loaded from environment variables prefixed with `AUTH_`. Create an `.env` file or export these before starting your app:

```bash
# Required
AUTH_JWT_SECRET_KEY=your-secret-key-at-least-32-bytes-long-here

# Optional (defaults shown)
AUTH_JWT_ALGORITHM=HS256
AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
AUTH_PASSWORD_HASH_ALGORITHM=bcrypt

# OAuth2 (optional — leave empty to disable)
AUTH_OAUTH2_GOOGLE_CLIENT_ID=
AUTH_OAUTH2_GOOGLE_CLIENT_SECRET=
AUTH_OAUTH2_GITHUB_CLIENT_ID=
AUTH_OAUTH2_GITHUB_CLIENT_SECRET=

# Session management
AUTH_SESSION_REVOCATION_ENABLED=true
```

The `AuthConfig` class uses `pydantic-settings` with `env_prefix="AUTH_"`:

```python
from smartvintaawesomekit.auth import AuthConfig

config = AuthConfig()  # reads from environment
print(config.jwt_secret_key)      # required — raises ValidationError if missing
print(config.jwt_algorithm)       # default: "HS256"
print(config.password_hash_algorithm)  # default: "bcrypt"
```

## Quick Start

Wire everything into a FastAPI app in ~15 lines:

```python
from fastapi import FastAPI
from smartvintaawesomekit.auth import AuthConfig, create_auth_dependencies

app = FastAPI()
config = AuthConfig()
deps = create_auth_dependencies(app)

# Add JWT middleware
app.add_middleware(deps["middleware"])

# Protected route
@app.get("/me")
async def me(user=deps["get_current_user"]):
    return {"user": user}
```

## Sub-Modules

### JWT (`smartvintaawesomekit.auth.jwt`)

Stateless token creation and validation. Supports access tokens (short-lived) and refresh tokens (long-lived).

```python
from smartvintaawesomekit.auth import AuthConfig, JWTManager

config = AuthConfig()
jwt_manager = JWTManager(config)

# Create token pair
tokens = jwt_manager.create_token_pair(subject="user-123")
print(tokens.access_token)   # short-lived JWT string
print(tokens.refresh_token)  # long-lived JWT string
print(tokens.expires_in)     # seconds until access token expires

# Add custom claims to access token
tokens = jwt_manager.create_token_pair(
    subject="user-123",
    claims={"roles": ["admin"], "org_id": "acme-corp"}
)

# Decode and validate (raises jwt.JWTError on invalid/expired)
payload = jwt_manager.decode_token(tokens.access_token)
print(payload["sub"])  # "user-123"

# Refresh — exchange valid refresh token for new pair
new_tokens = jwt_manager.refresh_access_token(tokens.refresh_token)

# Manual token creation with custom expiry
from datetime import timedelta
token = jwt_manager.create_access_token(
    subject="user-123",
    expires_delta=timedelta(hours=1)
)
```

**Token payload fields:**
- `sub` — subject (user ID)
- `iat` — issued at (UTC datetime)
- `exp` — expiration (UTC datetime)
- `jti` — unique token ID (UUID4)
- `type` — `"access"` or `"refresh"`

**Error handling:**
- `jwt.JWTError` — raised on invalid, expired, or tampered tokens
- `ValueError` — raised when `refresh_access_token` receives a non-refresh token

### Password Hashing (`smartvintaawesomekit.auth.password`)

Algorithm-agnostic password hashing with bcrypt (default) or argon2.

```python
from smartvintaawesomekit.auth import PasswordHasher

# Default: bcrypt
hasher = PasswordHasher()

# Hash a password
hashed = hasher.hash_password("my-secret-password")
print(hashed)  # "$2b$12$..."

# Verify (timing-safe via passlib)
assert hasher.verify_password("my-secret-password", hashed)
assert not hasher.verify_password("wrong-password", hashed)

# Check if hash needs re-computation (e.g., after algorithm upgrade)
if hasher.needs_rehash(hashed):
    new_hash = hasher.hash_password("my-secret-password")
    # store new_hash

# Use argon2 instead
argon2_hasher = PasswordHasher(algorithm="argon2")
hashed = argon2_hasher.hash_password("my-secret-password")
```

**Supported algorithms:** `bcrypt`, `argon2`
**Error handling:** `ValueError` raised for unsupported algorithms.

### OAuth2 (`smartvintaawesomekit.auth.oauth2`)

Authorization code flow for Google and GitHub. Handles state parameters for CSRF protection.

```python
from smartvintaawesomekit.auth import AuthConfig, get_provider

config = AuthConfig()

# Google OAuth2
google = get_provider("google", config, redirect_uri="https://myapp.com/callback/google")
auth_url = google.get_authorization_url(state="random-csrf-token")
# Redirect user to auth_url

# In your callback endpoint:
async def google_callback(code: str):
    token_data = await google.exchange_code(code)
    user_info = await google.get_user_info(token_data["access_token"])
    # user_info contains: id, email, name, picture, etc.

# GitHub OAuth2
github = get_provider("github", config, redirect_uri="https://myapp.com/callback/github")
auth_url = github.get_authorization_url(state="random-csrf-token")
# Redirect user to auth_url
```

**Provider details:**

| Provider | Scopes | Token URL | User Info URL |
|----------|--------|-----------|---------------|
| Google | `openid email profile` | `oauth2.googleapis.com/token` | `googleapis.com/oauth2/v2/userinfo` |
| GitHub | `read:user user:email` | `github.com/login/oauth/access_token` | `api.github.com/user` |

**Error handling:**
- `ValueError` — unknown provider name or missing credentials
- `httpx.TimeoutException` — provider not responding (10s timeout)
- `httpx.HTTPStatusError` — provider returned an error

### RBAC (`smartvintaawesomekit.auth.rbac`)

Role-based access control with hierarchical roles and FastAPI decorator integration.

```python
from smartvintaawesomekit.auth import RBACManager, require_role, require_permission

# Create manager and register roles
rbac = RBACManager()
rbac.register_role("editor", permissions={"posts:write", "posts:delete"})
rbac.register_role("superadmin", permissions={"users:manage"}, parent="editor")

# Check permissions programmatically
assert rbac.check_permission(["editor"], "posts:write")
assert rbac.check_permission(["superadmin"], "posts:delete")  # inherited from editor

# Use as FastAPI route decorators
@app.get("/admin/users")
@require_role("admin")
async def list_users(user=deps["get_current_user"]):
    return {"users": [...]}

@app.delete("/posts/{post_id}")
@require_permission("posts:delete")
async def delete_post(post_id: int, user=deps["get_current_user"]):
    return {"deleted": post_id}
```

**Built-in roles:** `admin`, `user`, `viewer`
**Error handling:** `HTTPException(403)` raised when role/permission check fails.

### Session Management (`smartvintaawesomekit.auth.session`)

Server-side refresh token tracking with revocation support. Uses SQLAlchemy for persistence.

```python
from smartvintaawesomekit.auth import AuthConfig, SessionManager

config = AuthConfig()

# Create session manager with async DB session
session_mgr = SessionManager(db=async_db_session, config=config)

# Create a session when issuing refresh tokens
session = await session_mgr.create_session(
    user_id="user-123",
    refresh_token_jti="uuid-from-refresh-token",
    user_agent="Mozilla/5.0 ...",
    ip_address="192.168.1.1",
)

# Look up session
session = await session_mgr.get_session(refresh_token_jti="uuid-from-refresh-token")

# Revoke a single session
revoked = await session_mgr.revoke_session(refresh_token_jti="uuid")

# Revoke all sessions for a user (e.g., password change)
count = await session_mgr.revoke_all_user_sessions(user_id="user-123")

# List active sessions
sessions = await session_mgr.list_active_sessions(user_id="user-123")

# Cleanup expired sessions (run periodically)
removed = await session_mgr.cleanup_expired()
```

**Session statuses:** `active`, `revoked`, `expired`

### Middleware (`smartvintaawesomekit.auth.middleware`)

FastAPI middleware that validates JWT from `Authorization: Bearer <token>` headers and injects the decoded payload into `request.state.user`.

```python
from smartvintaawesomekit.auth import AuthConfig, AuthMiddleware, JWTManager

config = AuthConfig()
jwt_manager = JWTManager(config)

# Create middleware with path skip list
middleware = AuthMiddleware(
    jwt_manager=jwt_manager,
    skip_paths=["/health", "/docs", "/openapi.json"],
)

# Add to FastAPI app
app = FastAPI()
app.add_middleware(AuthMiddleware, jwt_manager=jwt_manager, skip_paths=["/health"])
```

**Middleware behavior:**
1. Checks if request path matches any `skip_paths` prefix — skips auth if so
2. Extracts `Bearer <token>` from `Authorization` header
3. Decodes JWT via `JWTManager.decode_token()`
4. Sets `request.state.user` to decoded payload (or `None` on error)
5. Logs specific error types: `ExpiredSignatureError`, `InvalidTokenError`, generic `Exception`

### Dependencies (`smartvintaawesomekit.auth.middleware`)

Pre-configured FastAPI dependencies for route protection:

```python
from fastapi import FastAPI, Depends
from smartvintaawesomekit.auth import AuthConfig, create_auth_dependencies

app = FastAPI()
config = AuthConfig()
deps = create_auth_dependencies(config)

# Add middleware
app.add_middleware(deps["middleware"])

# Use in routes
@app.get("/profile")
async def profile(user=deps["get_current_user"]):
    """Requires valid JWT — returns 401 if not authenticated."""
    return {"user_id": user["sub"]}

@app.get("/admin/dashboard")
async def admin(user=deps["get_current_active_user"]):
    """Requires valid JWT + active account — returns 403 if inactive."""
    return {"admin": user["sub"]}
```

**`create_auth_dependencies(config)` returns:**
- `middleware` — `AuthMiddleware` instance
- `get_current_user` — dependency that returns user payload or raises 401
- `get_current_active_user` — dependency that checks active status, raises 403 if inactive

### ORM Models (`smartvintaawesomekit.auth.models`)

SQLAlchemy models for auth entities. Inherits from `smartvintaawesomekit.database.Base`.

| Model | Table | Key Fields |
|-------|-------|------------|
| `User` | `auth_users` | `id`, `email` (unique), `username` (unique), `hashed_password`, `is_active`, `is_verified` |
| `Role` | `auth_roles` | `id`, `name` (unique), `permissions` (JSON) |
| `UserRole` | `auth_user_roles` | `user_id` (FK), `role_id` (FK) — composite PK |
| `SessionRecord` | `auth_sessions` | `id`, `user_id` (FK), `refresh_token_jti` (unique), `status`, `user_agent`, `ip_address`, `created_at`, `expires_at` |

Create tables with:

```python
from smartvintaawesomekit.database import Base
from smartvintaawesomekit.auth.models import User, Role, UserRole, SessionRecord

async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

## Full Example

See `examples/auth_example.py` for a complete runnable example covering registration, login, token refresh, protected routes, RBAC, and OAuth2 integration.
