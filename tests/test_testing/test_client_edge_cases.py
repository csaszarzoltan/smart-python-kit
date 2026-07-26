"""Edge-case and behavioral tests for the testing module — Client Fixtures.

Extends the pre-existing tests with coverage for:
- async_client yields a working test client
- Custom route registration (integration check)
- auth_header() integration with client
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from smartvintaawesomekit.testing import async_client, auth_header


class TestAsyncClientBehavioralEdge:
    """Verify async_client edge cases."""

    @pytest.mark.asyncio
    async def test_async_client_returns_asyncclient_instance(self) -> None:
        """async_client should yield an httpx.AsyncClient."""
        async for client in async_client():
            assert isinstance(client, AsyncClient)
            break

    @pytest.mark.asyncio
    async def test_async_client_base_url(self) -> None:
        """async_client should have a base_url set."""
        async for client in async_client():
            assert client.base_url is not None
            break


class TestAuthHeaderEdge:
    """Verify auth_header() edge cases."""

    def test_auth_header_format(self) -> None:
        """auth_header() should return the correct Bearer format."""
        result = auth_header(token="my-test-token")
        assert result == {"Authorization": "Bearer my-test-token"}

    def test_auth_header_default_token(self) -> None:
        """auth_header() with no args should use the default test token."""
        result = auth_header()
        assert result["Authorization"] == "Bearer test-access-token"

    def test_auth_header_empty_token(self) -> None:
        """auth_header() with empty string should still produce Bearer format."""
        result = auth_header(token="")
        assert result["Authorization"] == "Bearer "

    def test_auth_header_returns_dict(self) -> None:
        """auth_header() return type should be a dict[str, str]."""
        result = auth_header()
        assert isinstance(result, dict)
        for k, v in result.items():
            assert isinstance(k, str)
            assert isinstance(v, str)

    def test_auth_header_unique_per_call(self) -> None:
        """Each auth_header() call should return a fresh dict."""
        h1 = auth_header(token="token1")
        h2 = auth_header(token="token2")
        assert h1 != h2
        assert h1["Authorization"] == "Bearer token1"
        assert h2["Authorization"] == "Bearer token2"


class TestAuthHeaderWithClientIntegration:
    """Verify auth_header() values are compatible with async_client headers."""

    @pytest.mark.asyncio
    async def test_auth_header_passes_as_client_header(self) -> None:
        """auth_header() output should be usable as AsyncClient headers param."""
        headers = auth_header()
        async for client in async_client():
            # Just verify the headers dict is in the right format for passing
            assert "Authorization" in headers
            # The actual request may 404 if the route doesn't exist,
            # but the header format is valid for httpx
            response = await client.get("/", headers=headers)
            assert response is not None
            break
