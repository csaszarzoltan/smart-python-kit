"""Model factories for test data generation.

Provides ``ModelFactory[T]`` base class and concrete factories for all
auth-domain models: User, Role, SessionRecord, and UserRole.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from smartvintaawesomekit.auth.models import Role, SessionRecord, User, UserRole

T = TypeVar("T")


class ModelFactory(Generic[T]):
    """Generic base factory for SQLAlchemy models.

    Class-level attributes:
        _model_class: The SQLAlchemy model type this factory produces.
        _defaults: Default field values used by ``build()`` and ``create()``.
        _model: Alias for ``_model_class`` used by some subclasses.

    Usage::

        class UserFactory(ModelFactory[User]):
            _model_class = User
            _defaults = {"email": "test@example.com", "username": "testuser"}
    """

    _model_class: type[T] | None = None
    _defaults: dict[str, Any] = {}
    Model: type[T] | None = None
    _model: type[T] | None = None

    @classmethod
    def build(cls, **overrides: Any) -> T:
        """Build a model instance in-memory with defaults + optional overrides.

        Args:
            **overrides: Field values to override the class defaults.

        Returns:
            A model instance populated with defaults + overrides.
        """
        legacy = overrides.pop("overrides", None)
        if legacy is not None:
            if not isinstance(legacy, dict):
                raise TypeError("overrides must be a mapping")
            overrides = {**legacy, **overrides}
        if cls._model_class is None:
            result: dict[str, Any] = {**cls._defaults, **overrides}
            return result  # type: ignore[return-value]
        instance = cls._model_class(**cls._defaults)
        for key, value in overrides.items():
            setattr(instance, key, value)
        return instance

    @classmethod
    async def create(cls, db_session: AsyncSession | None = None, **overrides: Any) -> T:
        """Build a model instance and persist it to the database.

        Args:
            db_session: An optional async SQLAlchemy session. When provided
                the instance is added and flushed.
            **overrides: Field values to override the class defaults.

        Returns:
            The persisted model instance.
        """
        instance = cls.build(**overrides)
        if db_session is not None:
            db_session.add(instance)
            await db_session.flush()
        return instance


class UserFactory(ModelFactory[User]):
    """Factory for creating ``User`` test instances."""

    _model_class = User
    _defaults: dict[str, Any] = {
        "email": "testuser@example.com",
        "username": "testuser",
        "hashed_password": "$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qm1Qm1Qm1Qm1Qm1Qm1Qm1Qm1Qm",  # noqa: E501
        "is_active": True,
        "is_verified": True,
    }


class RoleFactory(ModelFactory[Role]):
    """Factory for creating ``Role`` test instances."""

    _model_class = Role
    _defaults: dict[str, Any] = {
        "name": "test_role",
        "permissions": [],
    }


class SessionRecordFactory(ModelFactory[SessionRecord]):
    """Factory for creating ``SessionRecord`` test instances."""

    _model_class = SessionRecord
    _defaults: dict[str, Any] = {
        "user_id": 1,
        "refresh_token_jti": "test-jti-00000000-0000-0000-0000-000000000000",
        "status": "active",
        "expires_at": datetime.now(UTC) + timedelta(days=7),
    }


class UserRoleFactory(ModelFactory[UserRole]):
    """Factory for creating ``UserRole`` association test instances."""

    _model_class = UserRole
    _defaults: dict[str, Any] = {
        "user_id": 1,
        "role_id": 1,
    }
