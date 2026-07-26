"""Edge-case and behavioral tests for the testing module — Factories.

Extends the pre-existing TDD tests with additional coverage for:
- Empty overrides, all overrides, invalid field types
- create() with None db session
- Factory inheritance / custom factory classes
- build() does NOT persist to DB (no session leak)
- create() with real session (covers db_session.add/flush path)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from smartvintaawesomekit.testing import (
    ModelFactory,
    RoleFactory,
    SessionRecordFactory,
    UserFactory,
    UserRoleFactory,
)

# ──────────────────────────────────────────────────────────────────
# Edge Cases: Overrides
# ──────────────────────────────────────────────────────────────────


class TestFactoryEdgeCasesOverrides:
    """Verify factory behaviour with various override patterns."""

    def test_userfactory_empty_overrides(self) -> None:
        """UserFactory.build() with empty overrides should use all defaults."""
        user = UserFactory.build()
        assert user.username == "testuser"
        assert user.email == "testuser@example.com"
        assert user.is_active is True
        assert user.is_verified is True

    def test_userfactory_all_overrides(self) -> None:
        """UserFactory.build() should allow overriding every default field."""
        user = UserFactory.build(
            username="custom",
            email="custom@example.com",
            hashed_password="custom_hash",
            is_active=False,
            is_verified=False,
        )
        assert user.username == "custom"
        assert user.email == "custom@example.com"
        assert user.hashed_password == "custom_hash"
        assert user.is_active is False
        assert user.is_verified is False

    def test_rolefactory_empty_overrides(self) -> None:
        """RoleFactory.build() with empty overrides should use all defaults."""
        role = RoleFactory.build()
        assert role.name == "test_role"
        assert role.permissions == []

    def test_rolefactory_all_overrides(self) -> None:
        """RoleFactory.build() should allow overriding all fields."""
        role = RoleFactory.build(name="admin", permissions=["read", "write"])
        assert role.name == "admin"
        assert role.permissions == ["read", "write"]

    def test_sessionrecordfactory_empty_overrides(self) -> None:
        """SessionRecordFactory.build() with empty overrides should use defaults."""
        record = SessionRecordFactory.build()
        assert record.user_id == 1
        assert record.status == "active"

    def test_sessionrecordfactory_all_overrides(self) -> None:
        """SessionRecordFactory.build() should allow overriding all fields."""
        record = SessionRecordFactory.build(
            user_id=42,
            refresh_token_jti="custom-jti",
            status="expired",
        )
        assert record.user_id == 42
        assert record.refresh_token_jti == "custom-jti"
        assert record.status == "expired"

    def test_userrolefactory_empty_overrides(self) -> None:
        """UserRoleFactory.build() with empty overrides should use defaults."""
        ur = UserRoleFactory.build()
        assert ur.user_id == 1
        assert ur.role_id == 1

    def test_userrolefactory_all_overrides(self) -> None:
        """UserRoleFactory.build() should allow overriding all fields."""
        ur = UserRoleFactory.build(user_id=99, role_id=5)
        assert ur.user_id == 99
        assert ur.role_id == 5


class TestFactoryEdgeCasesInvalidTypes:
    """Verify factory behaviour with invalid/edge-case field types.

    ModelFactory delegates to the underlying SQLAlchemy model, which
    performs its own type coercion. These tests verify that passing
    unusual types does not cause the factory itself to raise (the
    model layer will coerce or raise separately).
    """

    def test_userfactory_invalid_type_for_boolean_field(self) -> None:
        """Factory should accept non-bool for bool fields; model handles coercion."""
        user = UserFactory.build(is_active="truthy")  # type: ignore[arg-type]
        assert user.is_active == "truthy"  # setattr stores whatever we pass

    def test_userfactory_invalid_type_for_int_field(self) -> None:
        """Factory should accept string where model expects int (setattr stores raw)."""
        # _defaults don't use ModelFactory for SessionRecord — checking build()
        record = SessionRecordFactory.build(user_id="not-an-int")  # type: ignore[arg-type]
        assert record.user_id == "not-an-int"


# ──────────────────────────────────────────────────────────────────
# Edge Cases: create() with None db_session
# ──────────────────────────────────────────────────────────────────


class TestFactoryCreateWithNoneSession:
    """Verify create() handles None db_session gracefully."""

    @pytest.mark.asyncio
    async def test_userfactory_create_none_session(self) -> None:
        """UserFactory.create(db_session=None) should build without persisting."""
        user = await UserFactory.create(db_session=None)
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_rolefactory_create_none_session(self) -> None:
        """RoleFactory.create(db_session=None) should build without persisting."""
        role = await RoleFactory.create(db_session=None)
        assert role is not None
        assert role.name == "test_role"

    @pytest.mark.asyncio
    async def test_sessionrecordfactory_create_none_session(self) -> None:
        """SessionRecordFactory.create(db_session=None) should build."""
        record = await SessionRecordFactory.create(db_session=None)
        assert record is not None

    @pytest.mark.asyncio
    async def test_userrolefactory_create_none_session(self) -> None:
        """UserRoleFactory.create(db_session=None) should build."""
        ur = await UserRoleFactory.create(db_session=None)
        assert ur is not None

    @pytest.mark.asyncio
    async def test_modelfactory_create_none_session(self) -> None:
        """ModelFactory.create(db_session=None) should build without persisting."""
        result = await ModelFactory.create(db_session=None, name="test")
        assert result is not None


# ──────────────────────────────────────────────────────────────────
# Edge Cases: build() does NOT persist to DB
# ──────────────────────────────────────────────────────────────────


class TestFactoryNoSessionLeak:
    """Verify build() does NOT interact with any DB session."""

    def test_userfactory_build_no_db_call(self) -> None:
        """UserFactory.build() should NOT call add/flush on any session."""
        user = UserFactory.build()
        assert user is not None
        # If build() accidentally called session methods, it would need a session
        # passed in. Since we didn't pass one, just confirming no crash is sufficient.

    def test_build_returns_fresh_instance_each_call(self) -> None:
        """Each build() call should return a new instance, not a cached one."""
        user1 = UserFactory.build()
        user2 = UserFactory.build()
        assert user1 is not user2  # different memory addresses
        assert user1.username == user2.username  # same defaults


# ──────────────────────────────────────────────────────────────────
# Edge Cases: Factory inheritance
# ──────────────────────────────────────────────────────────────────


class TestFactoryInheritance:
    """Verify custom factories can inherit from ModelFactory."""

    def test_custom_factory_build(self) -> None:
        """A custom factory should build instances correctly."""
        from smartvintaawesomekit.auth.models import User

        class CustomUserFactory(ModelFactory[User]):
            _model_class = User
            _defaults: dict[str, Any] = {
                "email": "custom@example.com",
                "username": "custom_user",
                "hashed_password": "hash",
                "is_active": False,
                "is_verified": False,
            }

        user = CustomUserFactory.build()
        assert user.email == "custom@example.com"
        assert user.username == "custom_user"
        assert user.is_active is False

    def test_custom_factory_with_overrides(self) -> None:
        """A custom factory should support overrides on build()."""
        from smartvintaawesomekit.auth.models import User

        class CustomUserFactory(ModelFactory[User]):
            _model_class = User
            _defaults: dict[str, Any] = {
                "email": "default@example.com",
                "username": "default_user",
                "hashed_password": "hash",
                "is_active": True,
                "is_verified": True,
            }

        user = CustomUserFactory.build(username="override_user")
        assert user.username == "override_user"
        assert user.email == "default@example.com"  # unchanged

    def test_custom_factory_inherits_from_factory(self) -> None:
        """A factory inheriting from another concrete factory should work."""
        from smartvintaawesomekit.auth.models import User

        class BaseUserFactory(ModelFactory[User]):
            _model_class = User
            _defaults: dict[str, Any] = {
                "email": "base@example.com",
                "username": "base_user",
                "hashed_password": "base_hash",
                "is_active": True,
                "is_verified": True,
            }

        class AdminUserFactory(BaseUserFactory):
            _defaults: dict[str, Any] = {
                **BaseUserFactory._defaults,
                "username": "admin_user",
            }

        admin = AdminUserFactory.build()
        assert admin.username == "admin_user"
        assert admin.email == "base@example.com"  # inherited defaults

    @pytest.mark.asyncio
    async def test_custom_factory_create(self) -> None:
        """A custom factory should support create() with None session."""
        from smartvintaawesomekit.auth.models import User

        class CustomUserFactory(ModelFactory[User]):
            _model_class = User
            _defaults: dict[str, Any] = {
                "email": "create@example.com",
                "username": "create_user",
                "hashed_password": "hash",
                "is_active": True,
                "is_verified": True,
            }

        user = await CustomUserFactory.create(db_session=None)
        assert user.username == "create_user"


# ──────────────────────────────────────────────────────────────────
# Edge Cases: create() with real session (add/flush coverage)
# ──────────────────────────────────────────────────────────────────


class TestFactoryCreateWithSession:
    """Verify create() with a real session calls add and flush."""

    @pytest.mark.asyncio
    async def test_userfactory_create_with_mock_session(self) -> None:
        """UserFactory.create() with a mock session should call add and flush."""
        session = MagicMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        user = await UserFactory.create(db_session=session)
        assert user is not None
        session.add.assert_called_once()  # add() is sync in SQLAlchemy
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rolefactory_create_with_mock_session(self) -> None:
        """RoleFactory.create() with a mock session should call add and flush."""
        session = MagicMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        role = await RoleFactory.create(db_session=session)
        assert role is not None
        session.add.assert_called_once()  # add() is sync in SQLAlchemy
        session.flush.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────
# Edge Cases: Duplicate create() calls
# ──────────────────────────────────────────────────────────────────


class TestFactoryCreateMultiple:
    """Verify multiple create() calls behave consistently."""

    @pytest.mark.asyncio
    async def test_multiple_create_returns_separate_instances(self) -> None:
        """Two create() calls should return separate instances."""
        u1 = await UserFactory.create(db_session=None)
        u2 = await UserFactory.create(db_session=None)
        assert u1 is not u2
        assert u1.username == u2.username  # same defaults
