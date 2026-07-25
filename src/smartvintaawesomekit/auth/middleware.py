"""FastAPI middleware and dependencies for injecting auth context."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, HTTPException, Request, Response

from smartvintaawesomekit.auth.config import AuthConfig
from smartvintaawesomekit.auth.jwt import JWTManager

if TYPE_CHECKING:
    from collections.abc import Callable


class AuthMiddleware:
    """FastAPI middleware that validates JWT and injects user into request.state."""

    def __init__(
        self,
        jwt_manager: JWTManager,
        skip_paths: list[str] | None = None,
    ) -> None:
        """Initialize auth middleware.

        Args:
            jwt_manager: JWTManager instance for token validation.
            skip_paths: List of path prefixes to skip authentication for.
        """
        self._jwt_manager: JWTManager = jwt_manager
        self._skip_paths: list[str] = skip_paths or []

    def _ensure_attrs(self) -> None:
        """Lazily initialize attributes when __init__ was skipped."""
        if not hasattr(self, "_jwt_manager"):
            self._jwt_manager = JWTManager(AuthConfig(jwt_secret_key="default"))
        if not hasattr(self, "_skip_paths"):
            self._skip_paths = []

    async def __call__(
        self,
        request: Request,
        call_next: Callable[..., Any],
    ) -> Response:
        """Process request — decode token, attach user to state, call next.

        Args:
            request: Incoming FastAPI request.
            call_next: Next middleware/handler in the chain.

        Returns:
            Response from the next handler.
        """
        self._ensure_attrs()
        # Skip auth for configured paths
        for path in self._skip_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header[7:]
        try:
            payload = self._jwt_manager.decode_token(token)
            request.state.user = payload
        except Exception:
            request.state.user = None

        return await call_next(request)


async def get_current_user(
    request: Request,
    jwt_manager: JWTManager = Depends(lambda: None),  # noqa: B008 — placeholder
) -> dict[str, Any]:
    """FastAPI dependency: extract current user from request.state. Raises HTTP 401 if missing.

    Args:
        request: Incoming FastAPI request.
        jwt_manager: JWTManager instance (injected via Depends).

    Returns:
        User payload dictionary.

    Raises:
        HTTPException: 401 if user is not authenticated.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_current_active_user(
    current_user: dict[str, Any] = Depends(lambda: None),  # noqa: B008 — placeholder
) -> dict[str, Any]:
    """Dependency: ensure current user is active. Raises HTTP 403 if inactive.

    Args:
        current_user: Current user payload (injected via Depends).

    Returns:
        Active user payload dictionary.

    Raises:
        HTTPException: 403 if user is inactive.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Check for active status in the user payload
    if current_user.get("active") is False:
        raise HTTPException(status_code=403, detail="User account is inactive")
    return current_user


def create_auth_dependencies(
    config: AuthConfig,
) -> dict[str, Any]:
    """Factory: create pre-configured auth dependencies for a FastAPI app.

    Returns dict with 'middleware', 'get_current_user', 'get_current_active_user'.

    Args:
        config: Auth configuration.

    Returns:
        Dictionary with pre-configured middleware and dependency callables.
    """
    jwt_manager = JWTManager(config)
    middleware = AuthMiddleware(jwt_manager)

    async def _get_current_user(request: Request) -> dict[str, Any]:
        return await get_current_user(request, jwt_manager=jwt_manager)

    async def _get_current_active_user(
        current_user: dict[str, Any] = Depends(_get_current_user),  # noqa: B008
    ) -> dict[str, Any]:
        return await get_current_active_user(current_user=current_user)

    return {
        "middleware": middleware,
        "get_current_user": _get_current_user,
        "get_current_active_user": _get_current_active_user,
    }


__all__ = [
    "AuthMiddleware",
    "get_current_user",
    "get_current_active_user",
    "create_auth_dependencies",
]
