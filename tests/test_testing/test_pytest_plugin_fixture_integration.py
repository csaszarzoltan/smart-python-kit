"""Integration tests for pytest plugin fixture wrappers.

These tests verify that the pytest-asyncio fixture wrappers in
pytest_plugin.py work correctly by using them via dependency injection.

This covers the yield statements in the fixture wrapper functions
(pytest_plugin.py lines 43-44, 50-51, 57-58).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


@pytest.mark.asyncio
async def test_db_engine_fixture_via_injection(db_engine: AsyncEngine) -> None:
    """db_engine fixture should yield an AsyncEngine."""
    assert db_engine is not None
    assert isinstance(db_engine, AsyncEngine)
    # Verify the engine can connect
    async with db_engine.begin() as conn:
        from sqlalchemy import text
        result = await conn.execute(text("SELECT 1"))
        assert result is not None


@pytest.mark.asyncio
async def test_db_session_fixture_via_injection(
    db_session: AsyncSession,  # type: ignore[no-untyped-def]
) -> None:
    """db_session fixture should yield a working session."""
    assert db_session is not None
    # Verify we can execute against the session
    from sqlalchemy import text
    result = await db_session.execute(text("SELECT 1"))
    assert result is not None


@pytest.mark.asyncio
async def test_async_client_fixture_via_injection(async_client: AsyncClient) -> None:
    """async_client fixture should yield an AsyncClient."""
    assert async_client is not None
    assert isinstance(async_client, AsyncClient)
    # Verify the client can make a request (may 404, that's OK)
    response = await async_client.get("/")
    assert response is not None


@pytest.mark.asyncio
async def test_all_fixtures_together(
    db_engine: AsyncEngine,
    db_session: AsyncSession,  # type: ignore[no-untyped-def]
    async_client: AsyncClient,
) -> None:
    """All three fixtures should work together without conflict."""
    assert db_engine is not None
    assert db_session is not None
    assert async_client is not None
    assert isinstance(db_engine, AsyncEngine)
    assert isinstance(async_client, AsyncClient)
