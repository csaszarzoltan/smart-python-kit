"""Mock implementations for database dependencies.

Provides ``MockAsyncSession`` and ``MockCRUD`` for testing database-
dependent code without a real SQLAlchemy engine.
"""

from __future__ import annotations

from typing import Any


class MockAsyncSession:
    """Fake async SQLAlchemy session for testing.

    Supports ``execute()``, ``add()``, ``flush()``, ``commit()``,
    ``rollback()``, and ``close()`` as coroutines.  All methods are
    no-ops that return sensible defaults.
    """

    def __init__(self) -> None:
        """Initialise the mock session."""
        self._added: list[Any] = []

    async def execute(self, statement: Any, **kwargs: Any) -> Any:
        """Simulate executing a SQL statement.

        Args:
            statement: The statement to execute (ignored in mock).
            **kwargs: Additional parameters (ignored).

        Returns:
            An object with ``scalar_one_or_none()``, ``scalars()`` and
            ``all()`` methods that return sensible defaults.
        """
        return _MockResult()

    async def add(self, instance: Any) -> None:
        """Simulate adding an object to the session.

        Args:
            instance: The model instance to add.
        """
        self._added.append(instance)

    async def flush(self) -> None:
        """Simulate flushing pending changes (no-op)."""
        pass

    async def commit(self) -> None:
        """Simulate committing the transaction (no-op)."""
        pass

    async def rollback(self) -> None:
        """Simulate rolling back the transaction (no-op)."""
        pass

    async def close(self) -> None:
        """Simulate closing the session (no-op)."""
        pass


class _MockResult:
    """Helper that provides the minimal ``Result`` interface expected by tests."""

    def scalar_one_or_none(self) -> Any:
        return None

    def scalars(self) -> _MockScalars:
        return _MockScalars()

    def all(self) -> list[Any]:
        return []


class _MockScalars:
    def all(self) -> list[Any]:
        return []


class MockCRUD:
    """Pre-configured CRUD mock for testing.

    Provides ``create()``, ``read()``, ``update()``, ``delete()``, and
    ``get_multi()`` as coroutines that return deterministic values.

    Pre-populated with a single default item (``id=1``) so that
    read/update/delete tests can operate without an explicit create
    step.
    """

    def __init__(self) -> None:
        """Initialise the mock CRUD with an in-memory store."""
        self._store: dict[int, dict[str, Any]] = {
            1: {"id": 1, "name": "default-item"},
        }
        self._next_id: int = 2

    async def create(
        self,
        db_session: Any = None,
        obj_in: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new item in the in-memory store.

        Args:
            db_session: Ignored in mock.
            obj_in: Data dict for the new item.

        Returns:
            The created item dict with an ``id`` field.
        """
        obj = dict(obj_in or {})
        obj["id"] = self._next_id
        self._store[self._next_id] = obj
        self._next_id += 1
        return obj

    async def read(
        self,
        db_session: Any = None,
        record_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Read an item from the in-memory store by id.

        Args:
            db_session: Ignored in mock.
            record_id: The item id.

        Returns:
            The item dict, or ``None`` if not found.
        """
        return self._store.get(record_id) if record_id is not None else None

    async def update(
        self,
        db_session: Any = None,
        record_id: int | None = None,
        obj_in: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Update an item in the in-memory store.

        Args:
            db_session: Ignored in mock.
            record_id: The item id.
            obj_in: Fields to update.

        Returns:
            The updated item dict, or ``None`` if not found.
        """
        if record_id not in self._store:
            return None
        obj = dict(obj_in or {})
        obj["id"] = record_id
        self._store[record_id] = obj
        return obj

    async def delete(
        self,
        db_session: Any = None,
        record_id: int | None = None,
    ) -> bool:
        """Delete an item from the in-memory store by id.

        Args:
            db_session: Ignored in mock.
            record_id: The item id.

        Returns:
            ``True`` if the item existed, ``False`` otherwise.
        """
        if record_id in self._store:
            del self._store[record_id]
            return True
        return False

    async def get_multi(
        self,
        db_session: Any = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List items from the in-memory store with pagination.

        Args:
            db_session: Ignored in mock.
            skip: Number of items to skip.
            limit: Maximum items to return.

        Returns:
            A list of item dicts.
        """
        items = list(self._store.values())
        return items[skip : skip + limit]
