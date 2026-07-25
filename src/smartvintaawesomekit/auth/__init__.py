"""Auth module — public API re-exports for convenience imports."""

from __future__ import annotations

from smartvintaawesomekit.auth.config import AuthConfig
from smartvintaawesomekit.auth.jwt import JWTManager, TokenPair
from smartvintaawesomekit.auth.middleware import (
    AuthMiddleware,
    create_auth_dependencies,
    get_current_active_user,
    get_current_user,
)
from smartvintaawesomekit.auth.oauth2 import (
    GitHubOAuth2,
    GoogleOAuth2,
    OAuth2Provider,
    get_provider,
)
from smartvintaawesomekit.auth.password import PasswordHasher
from smartvintaawesomekit.auth.rbac import (
    RBACManager,
    Role,
    require_permission,
    require_role,
)
from smartvintaawesomekit.auth.session import SessionManager, SessionStatus

__all__ = [
    "AuthConfig",
    "JWTManager",
    "TokenPair",
    "PasswordHasher",
    "OAuth2Provider",
    "GoogleOAuth2",
    "GitHubOAuth2",
    "get_provider",
    "Role",
    "RBACManager",
    "require_role",
    "require_permission",
    "SessionStatus",
    "SessionManager",
    "AuthMiddleware",
    "get_current_user",
    "get_current_active_user",
    "create_auth_dependencies",
]
