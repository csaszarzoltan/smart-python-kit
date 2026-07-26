"""Async database fixtures for pytest.

Provides in-memory SQLite engine and session fixtures that are scoped per test
and roll back automatically after each test.

Note: these are defined as raw async generator functions (no ``@pytest``
decorator) so they can be inspected and called directly by behavioral tests.
They are registered as pytest fixtures by the ``pytest_plugin`` module.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from smartvintaawesomekit.database import Base


async def db_engine() -> AsyncGenerator[Any, None]:
    """Create an in-memory SQLite async engine and create all tables.

    Yields:
        The SQLAlchemy async engine. Tables are created before the fixture
        yields and torn down after the fixture scope ends.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def db_session(  # type: ignore[no-untyped-def]
    _engine=None,
) -> AsyncGenerator[Any, None]:
    """Create a per-test database session that rolls back after the test.

    Yields:
        An async SQLAlchemy session. Tables are already created by
        ``db_engine``. After the test completes the session is closed.

    Args:
        _engine: An optional engine instance. If omitted, an in-memory
            SQLite engine is created automatically.
    """
    if _engine is not None:
        engine = _engine
    else:
        engine = create_async_engine(
            "sqlite+aiosqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    from sqlalchemy.ext.asyncio import AsyncSession

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session

    if _engine is None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
