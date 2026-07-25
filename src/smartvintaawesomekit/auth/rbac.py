"""Role-based access control with decorator-based route protection."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, Request

if TYPE_CHECKING:
    from collections.abc import Callable


class Role(StrEnum):
    """Built-in roles. Extensible via RBACManager."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class RBACManager:
    """Manages roles and permission checks."""

    def __init__(self) -> None:
        """Initialize RBAC manager with built-in roles."""
        self._init_roles()

    def _init_roles(self) -> None:
        """Set up the role registry."""
        self._roles: dict[str, dict[str, Any]] = {}
        # Register built-in roles
        self._roles["admin"] = {"permissions": set(), "parent": None}
        self._roles["user"] = {"permissions": set(), "parent": None}
        self._roles["viewer"] = {"permissions": set(), "parent": None}

    def _ensure_roles(self) -> None:
        """Lazily initialize roles when __init__ was skipped."""
        if not hasattr(self, "_roles"):
            self._init_roles()

    def register_role(self, name: str, permissions: set[str], parent: str | None = None) -> None:
        """Register a role with optional parent for inheritance.

        Args:
            name: Role name.
            permissions: Set of permission strings.
            parent: Optional parent role name for inheritance.
        """
        self._ensure_roles()
        if parent and parent not in self._roles:
            raise ValueError(f"Parent role '{parent}' does not exist")
        self._roles[name] = {"permissions": set(permissions), "parent": parent}

    def check_permission(self, user_roles: list[str], required_permission: str) -> bool:
        """Check if any of the user's roles grant the required permission.

        Args:
            user_roles: List of role names assigned to the user.
            required_permission: Permission string to check.

        Returns:
            True if any role grants the permission.
        """
        self._ensure_roles()
        perms = self.get_user_permissions(user_roles)
        return required_permission in perms

    def get_user_permissions(self, user_roles: list[str]) -> set[str]:
        """Compute the full permission set for a list of roles (including hierarchy).

        Args:
            user_roles: List of role names.

        Returns:
            Union of all permissions from all roles and their ancestors.
        """
        self._ensure_roles()
        all_permissions: set[str] = set()
        for role_name in user_roles:
            all_permissions |= self._get_role_permissions(role_name)
        return all_permissions

    def _get_role_permissions(self, role_name: str) -> set[str]:
        """Recursively collect permissions from a role and its ancestors.

        Args:
            role_name: Role name to collect permissions for.

        Returns:
            Set of all permissions including inherited ones.
        """
        if role_name not in self._roles:
            return set()
        role = self._roles[role_name]
        perms = set(role["permissions"])
        if role["parent"]:
            perms |= self._get_role_permissions(role["parent"])
        return perms


def require_role(*roles: str) -> Callable[..., Any]:
    """Decorator for FastAPI routes.

    Raises HTTP 403 Forbidden if user lacks any of the specified roles.

    Args:
        *roles: Allowed role names.

    Returns:
        Decorator function for FastAPI route handlers.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            request: Request | None = kwargs.get("request")
            if request is None and args:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if request is None or not hasattr(request.state, "user"):
                raise HTTPException(status_code=403, detail="Not authenticated")
            user_roles = request.state.user.get("roles", [])
            if not any(role in user_roles for role in roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required roles: {', '.join(roles)}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Module-level singleton to avoid recreating RBACManager per request
_default_rbac_manager = RBACManager()


def require_permission(permission: str) -> Callable[..., Any]:
    """Decorator for fine-grained permission checks. Raises HTTP 403 Forbidden if not granted.

    Args:
        permission: Required permission string.

    Returns:
        Decorator function for FastAPI route handlers.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            request: Request | None = kwargs.get("request")
            if request is None and args:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if request is None or not hasattr(request.state, "user"):
                raise HTTPException(status_code=403, detail="Not authenticated")
            user_roles = request.state.user.get("roles", [])
            if not _default_rbac_manager.check_permission(user_roles, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required permission: {permission}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["Role", "RBACManager", "require_role", "require_permission"]
