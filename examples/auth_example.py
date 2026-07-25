"""Complete auth example — registration, login, JWT, RBAC, session management.

Run with:
    AUTH_JWT_SECRET_KEY="your-secret-key-here-at-least-32-bytes" \\
    uvicorn examples.auth_example:app --reload

Test with:
    curl -X POST http://localhost:8000/register -H "Content-Type: application/json" \\
         -d '{"email": "alice@example.com", "username": "alice", "password": "secret123"}'

    curl -X POST http://localhost:8000/login -H "Content-Type: application/json" \\
         -d '{"email": "alice@example.com", "password": "secret123"}'

    # Use the access_token from /login in subsequent requests:
    curl http://localhost:8000/me -H "Authorization: Bearer <access_token>"
    curl http://localhost:8000/admin -H "Authorization: Bearer <access_token>"
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from smartvintaawesomekit.auth import (
    AuthConfig,
    JWTManager,
    PasswordHasher,
    RBACManager,
    create_auth_dependencies,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = FastAPI(title="Auth Example", version="0.2.0")
config = AuthConfig()
deps = create_auth_dependencies(config)
jwt_manager = JWTManager(config)
password_hasher = PasswordHasher(config.password_hash_algorithm)
rbac = RBACManager()

# Register RBAC roles
rbac.register_role("editor", permissions={"posts:write", "posts:delete"})
rbac.register_role("superadmin", permissions={"users:manage"}, parent="editor")

# Add middleware
app.add_middleware(deps["middleware"], skip_paths=["/health", "/docs"])

# In-memory user store (replace with database in production)
_users: dict[str, dict] = {}
_user_id_counter = 0

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Routes — public
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/register", response_model=dict)
async def register(req: RegisterRequest):
    """Register a new user with email, username, and password."""
    global _user_id_counter  # noqa: PLW0603

    if req.email in _users:
        raise HTTPException(status_code=409, detail="Email already registered")

    _user_id_counter += 1
    user = {
        "id": str(_user_id_counter),
        "email": req.email,
        "username": req.username,
        "hashed_password": password_hasher.hash_password(req.password),
        "roles": ["user"],
        "is_active": True,
    }
    _users[req.email] = user
    return {"id": user["id"], "email": user["email"], "username": user["username"]}


@app.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate and return JWT access + refresh token pair."""
    user = _users.get(req.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not password_hasher.verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = jwt_manager.create_token_pair(
        subject=user["id"],
        claims={"email": user["email"], "roles": user["roles"]},
    )
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@app.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    """Exchange a valid refresh token for a new token pair."""
    try:
        new_tokens = jwt_manager.refresh_access_token(req.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None

    return TokenResponse(
        access_token=new_tokens.access_token,
        refresh_token=new_tokens.refresh_token,
        token_type=new_tokens.token_type,
        expires_in=new_tokens.expires_in,
    )


# ---------------------------------------------------------------------------
# Routes — protected (require JWT)
# ---------------------------------------------------------------------------


@app.get("/me")
async def me(user: dict = Depends(deps["get_current_user"])):
    """Return the current authenticated user's payload."""
    return {
        "user_id": user["sub"],
        "email": user.get("email"),
        "roles": user.get("roles", []),
    }


@app.get("/admin")
async def admin(user: dict = Depends(deps["get_current_active_user"])):
    """Admin-only route — requires active account."""
    return {"message": f"Welcome admin {user['sub']}"}


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
