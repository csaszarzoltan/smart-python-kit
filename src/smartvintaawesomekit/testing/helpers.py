"""Test assertion helpers for API responses.

Provides ``assert_response()`` for validating standard API response shapes
and ``assert_paginated()`` for paginated list endpoints.
"""

from __future__ import annotations

from typing import Any


def assert_response(
    response: Any,
    expected_status: int = 200,
    data_key: str | None = None,
) -> bool:
    """Validate a standard API response.

    Checks that the response's status code matches ``expected_status``.
    When ``data_key`` is provided and the status is 2xx the key is
    checked for presence in the JSON body.

    Args:
        response: An object with ``.status_code`` and a ``.json()`` or
            ``.data`` attribute.
        expected_status: Expected HTTP status code. Default: 200.
        data_key: Optional key to verify exists in the response body.

    Returns:
        ``True`` when all checks pass.

    Raises:
        AssertionError: If any check fails.
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}"
    )

    if expected_status < 400 and data_key is not None:
        body = _get_body(response)
        assert data_key in body, (
            f"Expected key '{data_key}' in response body, got keys: {list(body.keys())}"
        )

    return True


def assert_paginated(
    response: Any,
    page: int = 1,
    size: int = 20,
) -> bool:
    """Validate a paginated API response.

    Checks that the response status is 200 and that standard pagination
    fields (``items``, ``total``, ``page``, ``size``) are present.

    Args:
        response: An object with ``.status_code`` and a ``.json()`` or
            ``.data`` attribute.
        page: Expected page number.
        size: Expected page size.

    Returns:
        ``True`` when all pagination checks pass.

    Raises:
        AssertionError: If any check fails.
    """
    assert response.status_code == 200, (
        f"Expected status 200 for paginated response, got {response.status_code}"
    )

    body = _get_body(response)
    assert "items" in body, "Paginated response must contain 'items'"
    assert "total" in body, "Paginated response must contain 'total'"
    assert "page" in body, "Paginated response must contain 'page'"
    assert "size" in body, "Paginated response must contain 'size'"

    assert body["page"] == page, f"Expected page {page}, got {body['page']}"
    assert body["size"] == size, f"Expected size {size}, got {body['size']}"

    return True


def _get_body(response: Any) -> dict[str, Any]:
    """Extract the JSON body from a response object."""
    if hasattr(response, "json") and callable(response.json):
        data = response.json()
        if isinstance(data, dict):
            return data
    if hasattr(response, "data") and isinstance(response.data, dict):
        return response.data
    return {}
