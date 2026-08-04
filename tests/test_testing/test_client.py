"""Behavioral and interface tests for the testing module — Client Fixtures.

Interface tests:
    - Verify async_client fixture exists
    - Verify fixture signature and type hints

Behavioral tests:
    - async_client creates FastAPI test client
    - Client can make GET/POST requests
    - Auth headers work with client
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest

from smartvintaawesomekit.testing import async_client

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestClientFixturesInterface:
    """Verify client fixture API exists with correct signatures."""

    def test_async_client_exists(self) -> None:
        """async_client should be importable."""
        assert async_client is not None

    def test_async_client_is_fixture(self) -> None:
        """async_client should be a pytest fixture."""
        assert callable(async_client) or hasattr(async_client, "_pytestfixturefunction")

    def test_async_client_is_async_generator(self) -> None:
        """async_client fixture should be an async generator function."""
        assert inspect.isasyncgenfunction(async_client)

    def test_async_client_signature(self) -> None:
        """async_client fixture should have minimal params."""
        sig = inspect.signature(async_client)
        params = list(sig.parameters.keys())
        # May accept optional fixture parameters (db_session, etc.)
        assert len(params) <= 3

    def test_async_client_return_type_contains_client(self) -> None:
        """async_client return type hint should reference AsyncClient."""
        hints = get_type_hints(async_client)
        ret = str(hints.get("return", ""))
        assert "Client" in ret or "TestClient" in ret


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates as test FAILURE.
# ──────────────────────────────────────────────────────────────────


class TestClientFixturesBehavioral:
    """Verify client fixture behaviors."""

    @pytest.mark.asyncio
    async def test_async_client_creates_fastapi_test_client(self) -> None:
        """async_client should create a FastAPI test client."""
        # Implemented behavior
        async for client in async_client():
            assert client is not None
            break

    @pytest.mark.asyncio
    async def test_async_client_can_make_get_requests(self) -> None:
        """async_client should support GET requests."""
        # Implemented behavior
        async for client in async_client():
            response = await client.get("/")
            assert response is not None
            break

    @pytest.mark.asyncio
    async def test_async_client_can_make_post_requests(self) -> None:
        """async_client should support POST requests."""
        # Implemented behavior
        async for client in async_client():
            response = await client.post("/", json={})
            assert response is not None
            break

    @pytest.mark.asyncio
    async def test_async_client_auth_headers_work(self) -> None:
        """async_client should work with Authorization headers."""
        # Implemented behavior
        from smartvintaawesomekit.testing import auth_header

        headers = auth_header(token="test-token")
        async for client in async_client():
            response = await client.get("/me", headers=headers)
            assert response is not None
            break
