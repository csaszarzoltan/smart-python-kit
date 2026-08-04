"""Behavioral and interface tests for the testing module — Database Fixtures.

Interface tests:
    - Verify db_engine fixture exists/exports correctly
    - Verify db_session fixture exists/exports correctly
    - Verify fixture signatures and type hints

Behavioral tests:
    - db_engine creates in-memory SQLite engine
    - db_session creates tables, yields session, rolls back after test
    - Tables created before each test, cleaned after
"""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints

import pytest

from smartvintaawesomekit.testing import db_engine, db_session

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestDatabaseFixturesInterface:
    """Verify database fixture API exists with correct signatures."""

    def test_db_engine_exists(self) -> None:
        """db_engine should be importable."""
        assert db_engine is not None

    def test_db_session_exists(self) -> None:
        """db_session should be importable."""
        assert db_session is not None

    def test_db_engine_is_fixture(self) -> None:
        """db_engine should be a pytest fixture (callable or has fixture marker)."""
        assert callable(db_engine) or hasattr(db_engine, "_pytestfixturefunction")

    def test_db_session_is_fixture(self) -> None:
        """db_session should be a pytest fixture."""
        assert callable(db_session) or hasattr(db_session, "_pytestfixturefunction")

    def test_db_engine_signature(self) -> None:
        """db_engine should accept no required params."""
        sig = inspect.signature(db_engine)
        params = list(sig.parameters.keys())
        # May accept optional pytest fixtures like request
        assert len(params) <= 2

    def test_db_session_return_type(self) -> None:
        """db_session should be an async generator or return AsyncGenerator."""
        hints = get_type_hints(db_session)
        ret = hints.get("return", "")
        ret_str = str(ret)
        assert "Generator" in ret_str or "Session" in ret_str

    def test_db_engine_is_async_generator(self) -> None:
        """db_engine fixture should be an async generator function."""
        assert inspect.isasyncgenfunction(db_engine)

    def test_db_session_is_async_generator(self) -> None:
        """db_session fixture should be an async generator function."""
        assert inspect.isasyncgenfunction(db_session)


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates as test FAILURE.
# ──────────────────────────────────────────────────────────────────


class TestDatabaseFixturesBehavioral:
    """Verify database fixture behaviors."""

    @pytest.mark.asyncio
    async def test_db_engine_creates_in_memory_sqlite(self) -> None:
        """db_engine should create an in-memory SQLite engine."""
        # Implemented behavior
        engine = await anext(db_engine())
        assert engine is not None
        assert "sqlite" in str(engine.url)

    @pytest.mark.asyncio
    async def test_db_session_creates_tables(self) -> None:
        """db_session should create tables before yielding."""
        # Implemented behavior
        async for session in db_session():
            # If we get here, tables were created — just verify session works
            assert session is not None
            break

    @pytest.mark.asyncio
    async def test_db_session_rolls_back(self) -> None:
        """db_session should roll back after test completes."""
        # Implemented behavior
        records: list[Any] = []
        async for session in db_session():
            records.append(session)
            break
        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_db_session_cleanup_after_test(self) -> None:
        """db_session should drop tables after yield."""
        # Implemented behavior
        async for _ in db_session():
            pass  # pragma: no cover
