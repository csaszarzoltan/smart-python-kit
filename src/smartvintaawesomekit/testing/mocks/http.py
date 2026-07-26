"""Mock implementations for HTTP dependencies.

Provides ``MockResponse`` and ``MockAsyncClient`` for testing code that
makes HTTP calls without hitting a real server.
"""

from __future__ import annotations

from typing import Any


class MockResponse:
    """Pre-built HTTP response for use in tests.

    Class-level defaults so ``hasattr(cls, ...)`` checks pass for the
    expected interface attributes.

    Attributes:
        status_code: HTTP status code.
        data: JSON-serialisable body dict.
        headers: Response headers dict.
    """

    status_code: int = 200
    headers: dict[str, str] = {}

    def __init__(
        self,
        status_code: int = 200,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialise a mock response.

        Args:
            status_code: HTTP status code (default: 200).
            data: JSON body dict (default: ``{}``).
            headers: Response headers (default: ``{}``).
        """
        self.status_code = status_code
        self.data = data or {}
        self.headers = headers or {}

    def json(self) -> dict[str, Any]:
        """Return the response body dict.

        Returns:
            The ``data`` dict.
        """
        return self.data


class MockAsyncClient:
    """Configurable async HTTP client mock for testing.

    Supports ``get``, ``post``, ``put``, and ``delete`` methods, each
    returning a ``MockResponse``. Responses can be configured per URL
    via ``set_response()``.
    """

    def __init__(self) -> None:
        """Initialise with an empty response registry."""
        self._responses: dict[str, MockResponse] = {}

    def set_response(self, url: str, response: MockResponse) -> None:
        """Register a mock response for a specific URL.

        Args:
            url: The URL path to match (e.g. ``"/users"``).
            response: The ``MockResponse`` to return when this URL is
                requested.
        """
        self._responses[url] = response

    def _get_response(self, url: str) -> MockResponse:
        """Look up a registered response or return a default 200 empty body."""
        return self._responses.get(url, MockResponse(status_code=200, data={}))

    async def get(self, url: str, **kwargs: Any) -> MockResponse:
        """Simulate an HTTP GET request.

        Args:
            url: The request URL.
            **kwargs: Additional request parameters (ignored).

        Returns:
            The configured ``MockResponse`` for this URL.
        """
        return self._get_response(url)

    async def post(self, url: str, **kwargs: Any) -> MockResponse:
        """Simulate an HTTP POST request.

        Args:
            url: The request URL.
            **kwargs: Additional request parameters (ignored).

        Returns:
            The configured ``MockResponse`` for this URL.
        """
        return self._get_response(url)

    async def put(self, url: str, **kwargs: Any) -> MockResponse:
        """Simulate an HTTP PUT request.

        Args:
            url: The request URL.
            **kwargs: Additional request parameters (ignored).

        Returns:
            The configured ``MockResponse`` for this URL.
        """
        return self._get_response(url)

    async def delete(self, url: str, **kwargs: Any) -> MockResponse:
        """Simulate an HTTP DELETE request.

        Args:
            url: The request URL.
            **kwargs: Additional request parameters (ignored).

        Returns:
            The configured ``MockResponse`` for this URL.
        """
        return self._get_response(url)
