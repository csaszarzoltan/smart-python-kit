"""Edge-case and behavioral tests for the testing module — Helpers.

Extends the pre-existing tests with coverage for:
- assert_response edge cases (various status codes, data_key present/missing)
- assert_paginated edge cases (different page/size)
"""

from __future__ import annotations

import pytest

from smartvintaawesomekit.testing import assert_paginated, assert_response

# ──────────────────────────────────────────────────────────────────
# Edge Cases: assert_response with various status codes
# ──────────────────────────────────────────────────────────────────


class TestAssertResponseEdgeCases:
    """Verify assert_response handles various status codes and data_key scenarios."""

    def test_assert_response_2xx_status(self) -> None:
        """assert_response should pass for any 2xx status."""
        class MockResponse:
            status_code = 201

        assert assert_response(MockResponse(), expected_status=201) is True

    def test_assert_response_4xx_status(self) -> None:
        """assert_response should pass for 4xx when expected."""
        class MockResponse:
            status_code = 404

        assert assert_response(MockResponse(), expected_status=404) is True

    def test_assert_response_5xx_status(self) -> None:
        """assert_response should pass for 5xx when expected."""
        class MockResponse:
            status_code = 500

        assert assert_response(MockResponse(), expected_status=500) is True

    def test_assert_response_raises_on_mismatch(self) -> None:
        """assert_response should raise AssertionError on status mismatch."""
        class MockResponse:
            status_code = 200

        with pytest.raises(AssertionError):
            assert_response(MockResponse(), expected_status=404)

    def test_assert_response_with_data_key_present(self) -> None:
        """assert_response should pass when data_key exists in 2xx response."""
        class MockResponse:
            status_code = 200
            _json = {"id": 1, "name": "test"}

            def json(self) -> dict:
                return self._json

        assert assert_response(MockResponse(), data_key="id") is True

    def test_assert_response_with_data_key_missing(self) -> None:
        """assert_response should raise when data_key missing from 2xx response."""
        class MockResponse:
            status_code = 200
            _json = {"id": 1}

            def json(self) -> dict:
                return self._json

        with pytest.raises(AssertionError):
            assert_response(MockResponse(), data_key="nonexistent")

    def test_assert_response_data_key_ignored_for_4xx(self) -> None:
        """assert_response should not check data_key for error status codes."""
        class MockResponse:
            status_code = 404
            _json = {"detail": "Not found"}

            def json(self) -> dict:
                return self._json

        # data_key is only validated when expected_status < 400
        assert assert_response(MockResponse(), expected_status=404, data_key="missing") is True

    def test_assert_response_with_data_attribute(self) -> None:
        """assert_response should handle response objects with .data attribute."""
        class MockResponse:
            status_code = 200
            data = {"message": "ok"}

        assert assert_response(MockResponse(), data_key="message") is True

    def test_assert_response_returns_true(self) -> None:
        """assert_response should return True on success."""
        class MockResponse:
            status_code = 200

        result = assert_response(MockResponse())
        assert result is True


# ──────────────────────────────────────────────────────────────────
# Edge Cases: assert_paginated
# ──────────────────────────────────────────────────────────────────


class TestAssertPaginatedEdgeCases:
    """Verify assert_paginated handles various page/size values."""

    def test_assert_paginated_defaults(self) -> None:
        """assert_paginated should validate default page=1, size=20."""
        class MockResponse:
            status_code = 200
            _json = {"items": [], "total": 0, "page": 1, "size": 20}

            def json(self) -> dict:
                return self._json

        assert assert_paginated(MockResponse()) is True

    def test_assert_paginated_custom_page_and_size(self) -> None:
        """assert_paginated should validate custom page and size."""
        class MockResponse:
            status_code = 200
            _json = {"items": [{"id": 1}], "total": 1, "page": 3, "size": 10}

            def json(self) -> dict:
                return self._json

        assert assert_paginated(MockResponse(), page=3, size=10) is True

    def test_assert_paginated_raises_on_missing_items(self) -> None:
        """assert_paginated should raise when items field is missing."""
        class MockResponse:
            status_code = 200
            _json = {"total": 0, "page": 1, "size": 20}

            def json(self) -> dict:
                return self._json

        with pytest.raises(AssertionError):
            assert_paginated(MockResponse())

    def test_assert_paginated_raises_on_missing_total(self) -> None:
        """assert_paginated should raise when total field is missing."""
        class MockResponse:
            status_code = 200
            _json = {"items": [], "page": 1, "size": 20}

            def json(self) -> dict:
                return self._json

        with pytest.raises(AssertionError):
            assert_paginated(MockResponse())

    def test_assert_paginated_raises_on_wrong_page(self) -> None:
        """assert_paginated should raise when page doesn't match."""
        class MockResponse:
            status_code = 200
            _json = {"items": [], "total": 0, "page": 2, "size": 20}

            def json(self) -> dict:
                return self._json

        with pytest.raises(AssertionError):
            assert_paginated(MockResponse(), page=1)

    def test_assert_paginated_raises_on_wrong_size(self) -> None:
        """assert_paginated should raise when size doesn't match."""
        class MockResponse:
            status_code = 200
            _json = {"items": [], "total": 0, "page": 1, "size": 50}

            def json(self) -> dict:
                return self._json

        with pytest.raises(AssertionError):
            assert_paginated(MockResponse(), size=20)

    def test_assert_paginated_raises_on_non_200(self) -> None:
        """assert_paginated should raise when status is not 200."""
        class MockResponse:
            status_code = 404

        with pytest.raises(AssertionError):
            assert_paginated(MockResponse())

    def test_assert_paginated_with_data_attribute(self) -> None:
        """assert_paginated should handle response with .data instead of .json()."""
        class MockResponse:
            status_code = 200
            data = {"items": [{"id": 1}], "total": 1, "page": 1, "size": 20}

        assert assert_paginated(MockResponse()) is True

    def test_assert_paginated_returns_true(self) -> None:
        """assert_paginated should return True on success."""
        class MockResponse:
            status_code = 200
            _json = {"items": [], "total": 0, "page": 1, "size": 20}

            def json(self) -> dict:
                return self._json

        result = assert_paginated(MockResponse())
        assert result is True


# ──────────────────────────────────────────────────────────────────
# Edge Cases: _get_body fallback (line 94)
# ──────────────────────────────────────────────────────────────────


class TestGetBodyFallback:
    """Verify _get_body() returns {} when response has neither json() nor data."""

    def test_response_without_json_or_data_returns_empty(self) -> None:
        """_get_body should return {} when response has no json() and no data."""
        # This covers helpers.py line 94 — the empty dict fallback
        class BareResponse:
            status_code = 200

        assert assert_response(BareResponse()) is True

    def test_response_with_only_status_code(self) -> None:
        """A response with only status_code should still pass assert_response."""
        class MinimalResponse:
            status_code = 200

        assert assert_response(MinimalResponse(), expected_status=200) is True

    def test_get_body_fallback_with_data_key(self) -> None:
        """When response has no json() or data, _get_body should return {}."""
        class BareResponse:
            status_code = 200

        # With a data_key, assert_response will call _get_body,
        # which should return {} and then fail to find the key
        with pytest.raises(AssertionError, match="Expected key 'id' in response body"):
            assert_response(BareResponse(), data_key="id")
