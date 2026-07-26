"""Edge-case and behavioral tests for Mock HTTP classes.

Extends the pre-existing tests with coverage for:
- MockAsyncClient returns configured response per URL
- POST requests with JSON body (kwargs ignored)
- Error responses (404, 500)
- MockResponse edge cases
"""

from __future__ import annotations

import pytest

from smartvintaawesomekit.testing.mocks import MockAsyncClient, MockResponse

# ──────────────────────────────────────────────────────────────────
# MockResponse Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockResponseEdgeCases:
    """Verify MockResponse edge cases."""

    def test_default_creation(self) -> None:
        """MockResponse with no args should default to 200 and empty data."""
        resp = MockResponse()
        assert resp.status_code == 200
        assert resp.data == {}
        assert resp.headers == {}

    def test_custom_status_and_data(self) -> None:
        """MockResponse should accept custom status and data."""
        resp = MockResponse(status_code=404, data={"detail": "Not found"})
        assert resp.status_code == 404
        assert resp.data == {"detail": "Not found"}

    def test_custom_headers(self) -> None:
        """MockResponse should accept custom headers."""
        resp = MockResponse(
            status_code=201,
            data={"id": 1},
            headers={"X-Custom": "value"},
        )
        assert resp.headers["X-Custom"] == "value"

    def test_json_method(self) -> None:
        """MockResponse.json() should return the data dict."""
        resp = MockResponse(data={"key": "val"})
        assert resp.json() == {"key": "val"}

    def test_json_on_empty_data(self) -> None:
        """MockResponse.json() with no data should return empty dict."""
        resp = MockResponse()
        assert resp.json() == {}

    def test_status_code_types(self) -> None:
        """MockResponse should handle various status code ranges."""
        for code in [200, 201, 204, 301, 400, 403, 404, 500, 502, 503]:
            resp = MockResponse(status_code=code)
            assert resp.status_code == code


# ──────────────────────────────────────────────────────────────────
# MockAsyncClient Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockAsyncClientEdgeCases:
    """Verify MockAsyncClient edge cases."""

    @pytest.mark.asyncio
    async def test_default_get_returns_200(self) -> None:
        """Default get() should return a 200 MockResponse."""
        client = MockAsyncClient()
        resp = await client.get("/any")
        assert resp.status_code == 200
        assert resp.data == {}

    @pytest.mark.asyncio
    async def test_configured_response_per_url(self) -> None:
        """set_response() should return configured response for matching URL."""
        client = MockAsyncClient()
        client.set_response("/users", MockResponse(status_code=200, data={"items": [{"id": 1}]}))
        client.set_response("/users/1", MockResponse(status_code=200, data={"id": 1}))

        resp = await client.get("/users")
        assert resp.data == {"items": [{"id": 1}]}

        resp = await client.get("/users/1")
        assert resp.data == {"id": 1}

    @pytest.mark.asyncio
    async def test_error_response_404(self) -> None:
        """set_response() with 404 should return the error response."""
        client = MockAsyncClient()
        client.set_response(
            "/notfound",
            MockResponse(status_code=404, data={"detail": "Not found"}),
        )
        resp = await client.get("/notfound")
        assert resp.status_code == 404
        assert resp.data["detail"] == "Not found"

    @pytest.mark.asyncio
    async def test_error_response_500(self) -> None:
        """set_response() with 500 should return the error response."""
        client = MockAsyncClient()
        client.set_response(
            "/error",
            MockResponse(status_code=500, data={"detail": "Server error"}),
        )
        resp = await client.get("/error")
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_post_with_json_body(self) -> None:
        """post() should return configured response regardless of json body."""
        client = MockAsyncClient()
        client.set_response(
            "/create",
            MockResponse(status_code=201, data={"id": 1}),
        )
        resp = await client.post("/create", json={"name": "test"})
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_put_returns_response(self) -> None:
        """put() should return configured response."""
        client = MockAsyncClient()
        client.set_response(
            "/items/1",
            MockResponse(status_code=200, data={"id": 1, "name": "updated"}),
        )
        resp = await client.put("/items/1", json={"name": "updated"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_returns_response(self) -> None:
        """delete() should return configured response."""
        client = MockAsyncClient()
        client.set_response(
            "/items/1",
            MockResponse(status_code=204),
        )
        resp = await client.delete("/items/1")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_unconfigured_url_returns_default(self) -> None:
        """GET on an unconfigured URL should return default 200."""
        client = MockAsyncClient()
        resp = await client.get("/never-configured")
        assert resp.status_code == 200
        assert resp.data == {}

    @pytest.mark.asyncio
    async def test_post_on_unconfigured_url(self) -> None:
        """POST on an unconfigured URL should return default 200."""
        client = MockAsyncClient()
        resp = await client.post("/unconfigured", json={"a": 1})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_multiple_methods_same_url(self) -> None:
        """Same URL with different HTTP methods should return same configured response."""
        client = MockAsyncClient()
        client.set_response("/resource", MockResponse(status_code=200, data={"ok": True}))
        get_resp = await client.get("/resource")
        post_resp = await client.post("/resource", json={})
        assert get_resp.data == {"ok": True}
        assert post_resp.data == {"ok": True}
