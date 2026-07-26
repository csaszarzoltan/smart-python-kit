"""Async HTTP test client fixture and auth helpers for FastAPI testing.

Provides a reusable ``async_client`` fixture backed by
``httpx.AsyncClient`` with the FastAPI ASGI transport, plus an
``auth_header()`` helper.

Note: ``async_client`` is defined as a raw async generator function
(no ``@pytest`` decorator) so it can be inspected and called directly
by behavioral tests. It is registered as a pytest fixture by the
``pytest_plugin`` module.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from httpx import ASGITransport, AsyncClient

from smartvintaawesomekit.app import app


async def async_client() -> AsyncIterator[AsyncClient]:
    """Create an async HTTP client against the FastAPI test app.

    Yields:
        An ``httpx.AsyncClient`` configured with the ASGI transport so
        requests are served without a live server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def auth_header(token: str = "test-access-token") -> dict[str, str]:
    """Build an ``Authorization`` header dict for test requests.

    Args:
        token: The bearer token value. Defaults to ``"test-access-token"``.

    Returns:
        A dict suitable for passing as ``headers`` to an ``AsyncClient`` call::

            client.get("/me", headers=auth_header())
    """
    return {"Authorization": f"Bearer {token}"}
