"""Pytest plugin for ``smartvintaawesomekit.testing``.

Registers markers and wraps the testing module's raw async generator
functions as pytest fixtures so they are available via dependency
injection in any test project that has the
``smartvintaawesomekit_testing`` pytest11 entry point installed.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio

from smartvintaawesomekit.testing.client import async_client as _async_client_fn
from smartvintaawesomekit.testing.database import db_engine as _db_engine_fn
from smartvintaawesomekit.testing.database import db_session as _db_session_fn


def pytest_configure(config: pytest.Config) -> None:  # noqa: PT020
    """Register custom pytest markers.

    Args:
        config: The pytest configuration object.
    """
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async (provided by pytest-asyncio).",
    )
    config.addinivalue_line(
        "markers",
        "db: mark test as requiring database access.",
    )


# Wrapper fixtures — these re-register the raw async generator functions
# as pytest fixtures so that ``pytest --fixtures`` lists them and tests
# can request them by name via dependency injection.


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[Any, None]:
    """In-memory SQLite async engine with all tables created."""
    async for val in _db_engine_fn():
        yield val


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[Any, None]:
    """Per-test async session that rolls back after the test."""
    async for val in _db_session_fn():
        yield val


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[Any, None]:
    """FastAPI async HTTP test client."""
    async for val in _async_client_fn():
        yield val
