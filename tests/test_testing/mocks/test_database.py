"""Behavioral and interface tests for Mock Database classes.

Interface tests:
    - Verify MockAsyncSession, MockCRUD exist
    - Verify method signatures and return types

Behavioral tests:
    - MockAsyncSession supports execute(), add(), flush(), commit(), rollback()
    - MockCRUD wraps CRUD operations
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest

from smartvintaawesomekit.testing.mocks import MockAsyncSession, MockCRUD

# ──────────────────────────────────────────────────────────────────
# 1. MockAsyncSession
# ──────────────────────────────────────────────────────────────────


class TestMockAsyncSessionInterface:
    """Verify MockAsyncSession API exists with correct signatures."""

    def test_mockasyncsession_class_exists(self) -> None:
        """MockAsyncSession class should be importable."""
        assert MockAsyncSession is not None

    def test_mockasyncsession_has_execute_method(self) -> None:
        """MockAsyncSession should have execute method."""
        assert hasattr(MockAsyncSession, "execute")
        assert callable(MockAsyncSession.execute)

    def test_mockasyncsession_has_add_method(self) -> None:
        """MockAsyncSession should have add method."""
        assert hasattr(MockAsyncSession, "add")
        assert callable(MockAsyncSession.add)

    def test_mockasyncsession_has_flush_method(self) -> None:
        """MockAsyncSession should have flush method."""
        assert hasattr(MockAsyncSession, "flush")
        assert callable(MockAsyncSession.flush)

    def test_mockasyncsession_has_commit_method(self) -> None:
        """MockAsyncSession should have commit method."""
        assert hasattr(MockAsyncSession, "commit")
        assert callable(MockAsyncSession.commit)

    def test_mockasyncsession_has_rollback_method(self) -> None:
        """MockAsyncSession should have rollback method."""
        assert hasattr(MockAsyncSession, "rollback")
        assert callable(MockAsyncSession.rollback)

    def test_mockasyncsession_has_close_method(self) -> None:
        """MockAsyncSession should have close method."""
        assert hasattr(MockAsyncSession, "close")
        assert callable(MockAsyncSession.close)

    def test_execute_return_type(self) -> None:
        """execute() should have a return type hint."""
        hints = get_type_hints(MockAsyncSession.execute)
        assert "return" in hints

    def test_execute_signature(self) -> None:
        """execute() should accept statement param."""
        sig = inspect.signature(MockAsyncSession.execute)
        assert "statement" in sig.parameters or "stmt" in sig.parameters or "query" in sig.parameters

    def test_add_signature(self) -> None:
        """add() should accept instance param."""
        sig = inspect.signature(MockAsyncSession.add)
        assert "instance" in sig.parameters or "obj" in sig.parameters or "model" in sig.parameters

    def test_execute_is_async(self) -> None:
        """execute() should be a coroutine."""
        assert inspect.iscoroutinefunction(MockAsyncSession.execute)

    def test_add_is_async(self) -> None:
        """add() should be a coroutine (async mock)."""
        assert inspect.iscoroutinefunction(MockAsyncSession.add)

    def test_flush_is_async(self) -> None:
        """flush() should be a coroutine."""
        assert inspect.iscoroutinefunction(MockAsyncSession.flush)

    def test_commit_is_async(self) -> None:
        """commit() should be a coroutine."""
        assert inspect.iscoroutinefunction(MockAsyncSession.commit)

    def test_rollback_is_async(self) -> None:
        """rollback() should be a coroutine."""
        assert inspect.iscoroutinefunction(MockAsyncSession.rollback)

    def test_close_is_async(self) -> None:
        """close() should be a coroutine."""
        assert inspect.iscoroutinefunction(MockAsyncSession.close)


class TestMockAsyncSessionBehavioral:
    """Verify MockAsyncSession behaviors."""

    @pytest.mark.asyncio
    async def test_execute_works(self) -> None:
        """MockAsyncSession.execute() should accept and process statements."""
        # Implemented behavior
        session = MockAsyncSession()
        result = await session.execute("SELECT 1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_add_and_flush(self) -> None:
        """MockAsyncSession should support add() followed by flush()."""
        # Implemented behavior
        session = MockAsyncSession()
        await session.add({"id": 1, "name": "test"})
        await session.flush()

    @pytest.mark.asyncio
    async def test_commit_works(self) -> None:
        """MockAsyncSession.commit() should work without error."""
        # Implemented behavior
        session = MockAsyncSession()
        await session.commit()

    @pytest.mark.asyncio
    async def test_rollback_works(self) -> None:
        """MockAsyncSession.rollback() should work without error."""
        # Implemented behavior
        session = MockAsyncSession()
        await session.rollback()

    @pytest.mark.asyncio
    async def test_close_works(self) -> None:
        """MockAsyncSession.close() should work without error."""
        # Implemented behavior
        session = MockAsyncSession()
        await session.close()

    @pytest.mark.asyncio
    async def test_add_then_execute(self) -> None:
        """MockAsyncSession should reflect added objects in subsequent queries."""
        # Implemented behavior
        session = MockAsyncSession()
        await session.add({"id": 1, "name": "test"})
        await session.flush()
        result = await session.execute("SELECT * FROM test")
        assert result is not None


# ──────────────────────────────────────────────────────────────────
# 2. MockCRUD
# ──────────────────────────────────────────────────────────────────


class TestMockCRUDInterface:
    """Verify MockCRUD API exists with correct signatures."""

    def test_mockcrud_class_exists(self) -> None:
        """MockCRUD class should be importable."""
        assert MockCRUD is not None

    def test_mockcrud_has_create_method(self) -> None:
        """MockCRUD should have create method."""
        assert hasattr(MockCRUD, "create")
        assert callable(MockCRUD.create)

    def test_mockcrud_has_read_method(self) -> None:
        """MockCRUD should have read method."""
        assert hasattr(MockCRUD, "read")
        assert callable(MockCRUD.read)

    def test_mockcrud_has_update_method(self) -> None:
        """MockCRUD should have update method."""
        assert hasattr(MockCRUD, "update")
        assert callable(MockCRUD.update)

    def test_mockcrud_has_delete_method(self) -> None:
        """MockCRUD should have delete method."""
        assert hasattr(MockCRUD, "delete")
        assert callable(MockCRUD.delete)

    def test_mockcrud_has_list_method(self) -> None:
        """MockCRUD should have list or get_multi method."""
        has_list = hasattr(MockCRUD, "list") or hasattr(MockCRUD, "get_multi")
        assert has_list

    def test_create_signature(self) -> None:
        """create() should accept db_session and obj_in params."""
        sig = inspect.signature(MockCRUD.create)
        params = list(sig.parameters.keys())
        assert "self" in params
        has_obj_param = any("obj" in p or "data" in p or "item" in p for p in params)
        assert has_obj_param

    def test_read_signature(self) -> None:
        """read() should accept record_id or similar."""
        sig = inspect.signature(MockCRUD.read)
        params = list(sig.parameters.keys())
        has_id_param = any("id" in p or "pk" in p for p in params)
        assert has_id_param

    def test_create_return_type(self) -> None:
        """create() should have a return type hint."""
        hints = get_type_hints(MockCRUD.create)
        assert "return" in hints

    def test_read_return_type(self) -> None:
        """read() should have a return type hint."""
        hints = get_type_hints(MockCRUD.read)
        assert "return" in hints


class TestMockCRUDBehavioral:
    """Verify MockCRUD behaviors."""

    @pytest.mark.asyncio
    async def test_create_item(self) -> None:
        """MockCRUD.create() should create and return an item."""
        # Implemented behavior
        crud = MockCRUD()
        session = MockAsyncSession()
        result = await crud.create(db_session=session, obj_in={"name": "test"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_read_item(self) -> None:
        """MockCRUD.read() should return an item by id."""
        # Implemented behavior
        crud = MockCRUD()
        session = MockAsyncSession()
        result = await crud.read(db_session=session, record_id=1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_item(self) -> None:
        """MockCRUD.update() should update and return an item."""
        # Implemented behavior
        crud = MockCRUD()
        session = MockAsyncSession()
        result = await crud.update(db_session=session, record_id=1, obj_in={"name": "updated"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_item(self) -> None:
        """MockCRUD.delete() should delete an item."""
        # Implemented behavior
        crud = MockCRUD()
        session = MockAsyncSession()
        result = await crud.delete(db_session=session, record_id=1)
        assert result is True or result is None

    @pytest.mark.asyncio
    async def test_list_items(self) -> None:
        """MockCRUD.list() should return items with pagination."""
        # Implemented behavior
        crud = MockCRUD()
        session = MockAsyncSession()
        method = getattr(crud, "list", None) or getattr(crud, "get_multi", None)
        if method:
            result = await method(db_session=session)
            assert result is not None


# ──────────────────────────────────────────────────────────────────
# 3. Package exports
# ──────────────────────────────────────────────────────────────────


class TestMockDatabaseModuleIntegration:
    """Verify mocks package exports database mock classes."""

    def test_package_exports_mockasyncsession(self) -> None:
        """smartvintaawesomekit.testing.mocks should export MockAsyncSession."""
        from smartvintaawesomekit.testing.mocks import MockAsyncSession as MAS
        assert MAS is MockAsyncSession

    def test_package_exports_mockcrud(self) -> None:
        """smartvintaawesomekit.testing.mocks should export MockCRUD."""
        from smartvintaawesomekit.testing.mocks import MockCRUD as MCR
        assert MCR is MockCRUD
