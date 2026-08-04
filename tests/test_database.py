"""Behavioral and interface tests for the database module.

Interface tests:
    - Verify imports work
    - Verify classes exist and are callable
    - Verify method signatures and type hints

Behavioral tests:
    - get_session() raises
    - CRUD operations raise
    - CRUD instantiation raises
"""

from __future__ import annotations

from typing import get_type_hints

import pytest

from smartvintaawesomekit.database import CRUD, Base, get_session

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────

class TestDatabaseInterface:
    """Verify database module public API exists with correct signatures."""

    def test_base_class_exists(self) -> None:
        """Base class should be importable."""
        assert Base is not None

    def test_crud_class_exists(self) -> None:
        """CRUD class should be importable."""
        assert CRUD is not None

    def test_get_session_function_exists(self) -> None:
        """get_session function should be importable."""
        assert get_session is not None

    def test_base_inherits_declarative_base(self) -> None:
        """Base should inherit from DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(Base, DeclarativeBase)

    def test_crud_is_generic(self) -> None:
        """CRUD should be a generic class (accepts type params)."""
        # CRUD is generic over ModelType, CreateSchemaType, UpdateSchemaType
        assert hasattr(CRUD, "__class_getitem__") or hasattr(CRUD, "__orig_bases__")

    def test_crud_init_accepts_model(self) -> None:
        """CRUD.__init__ should accept a model class parameter."""
        import inspect
        sig = inspect.signature(CRUD.__init__)
        param_names = list(sig.parameters.keys())
        assert "model" in param_names[1:]  # skip self

    def test_crud_has_create_method(self) -> None:
        """CRUD should have a create method."""
        assert hasattr(CRUD, "create")
        assert callable(CRUD.create)

    def test_crud_has_read_method(self) -> None:
        """CRUD should have a read method."""
        assert hasattr(CRUD, "read")
        assert callable(CRUD.read)

    def test_crud_has_update_method(self) -> None:
        """CRUD should have an update method."""
        assert hasattr(CRUD, "update")
        assert callable(CRUD.update)

    def test_crud_has_delete_method(self) -> None:
        """CRUD should have a delete method."""
        assert hasattr(CRUD, "delete")
        assert callable(CRUD.delete)

    def test_crud_has_get_multi_method(self) -> None:
        """CRUD should have a get_multi method."""
        assert hasattr(CRUD, "get_multi")
        assert callable(CRUD.get_multi)

    def test_get_session_is_async_gen(self) -> None:
        """get_session should be an async generator function."""
        import inspect
        assert inspect.isasyncgenfunction(get_session)

    def test_crud_create_signature(self) -> None:
        """CRUD.create should accept db and obj_in parameters."""
        import inspect
        sig = inspect.signature(CRUD.create)
        param_names = list(sig.parameters.keys())
        assert "db" in param_names[1:]
        assert "obj_in" in param_names[1:]

    def test_crud_read_signature(self) -> None:
        """CRUD.read should accept db and id parameters."""
        import inspect
        sig = inspect.signature(CRUD.read)
        param_names = list(sig.parameters.keys())
        assert "db" in param_names[1:]
        assert "record_id" in param_names[1:]

    def test_crud_update_signature(self) -> None:
        """CRUD.update should accept db, db_obj, and obj_in."""
        import inspect
        sig = inspect.signature(CRUD.update)
        param_names = list(sig.parameters.keys())
        assert "db" in param_names[1:]
        assert "db_obj" in param_names[1:]
        assert "obj_in" in param_names[1:]

    def test_crud_delete_signature(self) -> None:
        """CRUD.delete should accept db and id."""
        import inspect
        sig = inspect.signature(CRUD.delete)
        param_names = list(sig.parameters.keys())
        assert "db" in param_names[1:]
        assert "record_id" in param_names[1:]

    def test_crud_get_multi_signature(self) -> None:
        """CRUD.get_multi should accept db, skip, and limit."""
        import inspect
        sig = inspect.signature(CRUD.get_multi)
        param_names = list(sig.parameters.keys())
        assert "db" in param_names[1:]
        assert "skip" in param_names[1:]
        assert "limit" in param_names[1:]

    def test_all_exports_listed(self) -> None:
        """Verify __all__ exports match expected public API."""
        from smartvintaawesomekit import database
        exports = database.__all__
        assert "Base" in exports
        assert "get_session" in exports
        assert "CRUD" in exports

    def test_crud_create_return_type(self) -> None:
        """CRUD.create return type should reference ModelType."""
        hints = get_type_hints(CRUD.create)
        assert "return" in hints

    def test_crud_read_return_type(self) -> None:
        """CRUD.read should return Optional[ModelType]."""
        hints = get_type_hints(CRUD.read)
        assert "return" in hints

    def test_crud_get_multi_return_type(self) -> None:
        """CRUD.get_multi should return list[ModelType]."""
        hints = get_type_hints(CRUD.get_multi)
        assert "return" in hints


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates as test FAILURE.
# ──────────────────────────────────────────────────────────────────

class TestDatabaseBehavioral:
    """Verify database module behaviors are stubbed — all should raise NotImplementedError."""

    @pytest.mark.asyncio
    async def test_get_session_not_implemented(self) -> None:
        """get_session should raise NotImplementedError."""
        async for _ in get_session():
            pass  # pragma: no cover

    def test_crud_instantiation_not_implemented(self) -> None:
        """CRUD instantiation should raise NotImplementedError."""
        CRUD(model=Base)  # type: ignore[type-var]

    @pytest.mark.asyncio
    async def test_crud_create_not_implemented(self) -> None:
        """CRUD.create should raise NotImplementedError."""
        crud = CRUD[None, None, None](model=Base)  # type: ignore[arg-type]
        await crud.create(db=None, obj_in=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_crud_read_not_implemented(self) -> None:
        """CRUD.read should raise NotImplementedError."""
        crud = CRUD[None, None, None](model=Base)  # type: ignore[arg-type]
        await crud.read(db=None, record_id=1)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_crud_update_not_implemented(self) -> None:
        """CRUD.update should raise NotImplementedError."""
        crud = CRUD[None, None, None](model=Base)  # type: ignore[arg-type]
        await crud.update(db=None, db_obj=None, obj_in=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_crud_delete_not_implemented(self) -> None:
        """CRUD.delete should raise NotImplementedError."""
        crud = CRUD[None, None, None](model=Base)  # type: ignore[arg-type]
        await crud.delete(db=None, record_id=1)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_crud_get_multi_not_implemented(self) -> None:
        """CRUD.get_multi should raise NotImplementedError."""
        crud = CRUD[None, None, None](model=Base)  # type: ignore[arg-type]
        await crud.get_multi(db=None)  # type: ignore[arg-type]
