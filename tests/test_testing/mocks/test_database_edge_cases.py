"""Edge-case and behavioral tests for Mock Database classes.

Extends the pre-existing tests with coverage for:
- Session lifecycle: add → flush → commit → rollback → close
- CRUD operations return sensible values
- Edge: method chaining, multiple operations
"""

from __future__ import annotations

import pytest

from smartvintaawesomekit.testing.mocks import MockAsyncSession, MockCRUD

# ──────────────────────────────────────────────────────────────────
# MockAsyncSession Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockAsyncSessionEdgeCases:
    """Verify MockAsyncSession edge cases beyond basic interface checks."""

    @pytest.mark.asyncio
    async def test_add_tracks_instances(self) -> None:
        """add() should track the instances added to the session."""
        session = MockAsyncSession()
        await session.add({"id": 1, "name": "test"})
        await session.add({"id": 2, "name": "test2"})
        assert len(session._added) == 2  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_add_after_flush(self) -> None:
        """add() followed by flush() should not raise."""
        session = MockAsyncSession()
        await session.add({"id": 1})
        await session.flush()  # should be no-op
        assert True

    @pytest.mark.asyncio
    async def test_full_lifecycle(self) -> None:
        """Session lifecycle: add → flush → commit → rollback → close."""
        session = MockAsyncSession()
        await session.add({"id": 1})
        await session.flush()
        await session.commit()
        await session.rollback()
        await session.close()
        # All operations are no-ops — just confirm no exception raised
        assert True

    @pytest.mark.asyncio
    async def test_execute_returns_result_object(self) -> None:
        """execute() should return an object with scalar_one_or_none, scalars, all."""
        session = MockAsyncSession()
        result = await session.execute("SELECT 1")
        assert hasattr(result, "scalar_one_or_none")
        assert hasattr(result, "scalars")
        assert hasattr(result, "all")

    @pytest.mark.asyncio
    async def test_execute_result_scalar_one_or_none_returns_none(self) -> None:
        """execute() result.scalar_one_or_none() should return None by default."""
        session = MockAsyncSession()
        result = await session.execute("SELECT 1")
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_execute_result_scalars_all_empty(self) -> None:
        """execute() result.scalars().all() should return empty list."""
        session = MockAsyncSession()
        result = await session.execute("SELECT 1")
        assert result.scalars().all() == []

    @pytest.mark.asyncio
    async def test_execute_result_all_empty(self) -> None:
        """execute() result.all() should return empty list."""
        session = MockAsyncSession()
        result = await session.execute("SELECT 1")
        assert result.all() == []

    @pytest.mark.asyncio
    async def test_multiple_adds_same_instance_type(self) -> None:
        """Multiple add() calls should each be tracked."""
        session = MockAsyncSession()
        for i in range(5):
            await session.add({"id": i})
        assert len(session._added) == 5  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_commit_then_add(self) -> None:
        """add() after commit() should work (session not closed)."""
        session = MockAsyncSession()
        await session.commit()
        await session.add({"id": 2})
        await session.flush()
        assert True

    @pytest.mark.asyncio
    async def test_close_then_add(self) -> None:
        """add() after close() should still work (mock doesn't enforce lifecycle)."""
        session = MockAsyncSession()
        await session.close()
        await session.add({"id": 3})  # should not raise
        assert True

    @pytest.mark.asyncio
    async def test_rollback_after_commit(self) -> None:
        """rollback() after commit() should not raise."""
        session = MockAsyncSession()
        await session.commit()
        await session.rollback()
        assert True

    @pytest.mark.asyncio
    async def test_multiple_execute_calls(self) -> None:
        """Multiple execute() calls should all return fresh result objects."""
        session = MockAsyncSession()
        r1 = await session.execute("Q1")
        r2 = await session.execute("Q2")
        assert r1 is not r2


# ──────────────────────────────────────────────────────────────────
# MockCRUD Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockCRUDEdgeCases:
    """Verify MockCRUD edge cases."""

    @pytest.mark.asyncio
    async def test_create_adds_to_store(self) -> None:
        """create() should add an item to the in-memory store."""
        crud = MockCRUD()
        item = await crud.create(db_session=None, obj_in={"name": "new-item"})
        assert item["id"] == 2  # auto-incremented from 2
        assert item["name"] == "new-item"

    @pytest.mark.asyncio
    async def test_read_existing_item(self) -> None:
        """read() should return an existing item."""
        crud = MockCRUD()
        item = await crud.read(db_session=None, record_id=1)
        assert item is not None
        assert item["id"] == 1
        assert item["name"] == "default-item"

    @pytest.mark.asyncio
    async def test_read_nonexistent_item(self) -> None:
        """read() should return None for non-existing id."""
        crud = MockCRUD()
        item = await crud.read(db_session=None, record_id=999)
        assert item is None

    @pytest.mark.asyncio
    async def test_update_existing_item(self) -> None:
        """update() should modify an existing item."""
        crud = MockCRUD()
        updated = await crud.update(db_session=None, record_id=1, obj_in={"name": "updated"})
        assert updated is not None
        assert updated["name"] == "updated"
        assert updated["id"] == 1

    @pytest.mark.asyncio
    async def test_update_nonexistent_item(self) -> None:
        """update() should return None for non-existing id."""
        crud = MockCRUD()
        result = await crud.update(db_session=None, record_id=999, obj_in={"name": "nope"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing_item(self) -> None:
        """delete() should return True for existing item."""
        crud = MockCRUD()
        result = await crud.delete(db_session=None, record_id=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_item(self) -> None:
        """delete() should return False for non-existing id."""
        crud = MockCRUD()
        result = await crud.delete(db_session=None, record_id=999)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_multi_returns_all(self) -> None:
        """get_multi() should return all items."""
        crud = MockCRUD()
        items = await crud.get_multi(db_session=None)
        assert len(items) == 1  # default item
        assert items[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_get_multi_with_pagination(self) -> None:
        """get_multi() should support skip/limit pagination."""
        crud = MockCRUD()
        await crud.create(db_session=None, obj_in={"name": "item2"})
        await crud.create(db_session=None, obj_in={"name": "item3"})

        items = await crud.get_multi(db_session=None, skip=0, limit=2)
        assert len(items) == 2

        items = await crud.get_multi(db_session=None, skip=1, limit=1)
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_crud_lifecycle(self) -> None:
        """Full CRUD lifecycle: create → read → update → read → delete."""
        crud = MockCRUD()
        # Create
        created = await crud.create(db_session=None, obj_in={"name": "lifecycle"})
        cid = created["id"]
        assert cid > 1

        # Read
        read_back = await crud.read(db_session=None, record_id=cid)
        assert read_back["name"] == "lifecycle"

        # Update
        await crud.update(db_session=None, record_id=cid, obj_in={"name": "updated-lifecycle"})
        updated = await crud.read(db_session=None, record_id=cid)
        assert updated is not None
        assert updated["name"] == "updated-lifecycle"

        # Delete
        deleted = await crud.delete(db_session=None, record_id=cid)
        assert deleted is True

        # Verify gone
        gone = await crud.read(db_session=None, record_id=cid)
        assert gone is None

    @pytest.mark.asyncio
    async def test_create_with_empty_obj_in(self) -> None:
        """create() with empty obj_in should still work."""
        crud = MockCRUD()
        item = await crud.create(db_session=None, obj_in={})
        assert item["id"] is not None

    @pytest.mark.asyncio
    async def test_create_with_none_obj_in(self) -> None:
        """create() with None obj_in should still work."""
        crud = MockCRUD()
        item = await crud.create(db_session=None, obj_in=None)
        assert item["id"] is not None
