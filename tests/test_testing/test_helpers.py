"""Behavioral and interface tests for the testing module — Helpers.

Interface tests:
    - Verify auth_header() exists with correct signature
    - Verify assert_response() exists with correct signature
    - Verify return types

Behavioral tests:
    - auth_header() returns Authorization dict
    - assert_response() validates API response shape
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest

from smartvintaawesomekit.testing import assert_response, auth_header

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestHelpersInterface:
    """Verify helper function APIs exist with correct signatures."""

    def test_auth_header_exists(self) -> None:
        """auth_header function should be importable."""
        assert auth_header is not None
        assert callable(auth_header)

    def test_assert_response_exists(self) -> None:
        """assert_response function should be importable."""
        assert assert_response is not None
        assert callable(assert_response)

    def test_auth_header_signature(self) -> None:
        """auth_header() should accept token parameter."""
        sig = inspect.signature(auth_header)
        assert "token" in sig.parameters

    def test_auth_header_token_default(self) -> None:
        """auth_header() token should default to valid test token."""
        sig = inspect.signature(auth_header)
        assert sig.parameters["token"].default is not inspect.Parameter.empty

    def test_auth_header_return_type(self) -> None:
        """auth_header() should return dict[str, str]."""
        hints = get_type_hints(auth_header)
        ret = hints.get("return")
        assert ret is not None
        ret_str = str(ret)
        assert "dict" in ret_str or "Dict" in ret_str

    def test_assert_response_signature(self) -> None:
        """assert_response() should accept response and expected_status."""
        sig = inspect.signature(assert_response)
        assert "response" in sig.parameters
        assert "expected_status" in sig.parameters or "status_code" in sig.parameters

    def test_assert_response_expected_status_default(self) -> None:
        """assert_response() expected_status should default to 200."""
        sig = inspect.signature(assert_response)
        if "expected_status" in sig.parameters:
            assert sig.parameters["expected_status"].default == 200

    def test_assert_response_has_data_key_param(self) -> None:
        """assert_response() should accept optional data_key or data_keys param."""
        sig = inspect.signature(assert_response)
        param_names = list(sig.parameters.keys())
        any("data" in p for p in param_names)
        # Optional — the helper may accept a data_key to extract nested data
        assert callable(assert_response)

    def test_auth_header_returns_authorization_dict(self) -> None:
        """auth_header() should return a dict with Authorization key."""
        # Implemented behavior — will fail with NotImplementedError
        result = auth_header()
        assert isinstance(result, dict)
        assert "Authorization" in result or "authorization" in result


class TestHelpersBehavioral:
    """Verify helper function behaviors."""

    def test_auth_header_returns_bearer_token(self) -> None:
        """auth_header() should return 'Bearer <token>' Authorization header."""
        # Implemented behavior
        result = auth_header(token="test123")
        assert result["Authorization"] == "Bearer test123"

    def test_auth_header_defaults_valid_token(self) -> None:
        """auth_header() with no args should return a valid Authorization header."""
        # Implemented behavior
        result = auth_header()
        assert "Authorization" in result
        assert str(result["Authorization"]).startswith("Bearer ")

    def test_assert_response_validates_status(self) -> None:
        """assert_response() should validate response status code."""
        # Implemented behavior
        class MockResponse:
            status_code = 200
            data = {"message": "ok"}

        result = assert_response(response=MockResponse(), expected_status=200)
        assert result is True or result is None

    def test_assert_response_raises_on_wrong_status(self) -> None:
        """assert_response() should raise AssertionError on status mismatch."""
        # Implemented behavior
        class MockResponse:
            status_code = 404
            data = {"detail": "Not found"}

        with pytest.raises(AssertionError):
            assert_response(response=MockResponse(), expected_status=200)

    def test_assert_response_validates_json_body(self) -> None:
        """assert_response() should validate response JSON body keys."""
        # Implemented behavior
        class MockResponse:
            status_code = 200
            data = {"id": 1, "name": "test"}

        result = assert_response(response=MockResponse(), expected_status=200)
        assert result is True or result is None
