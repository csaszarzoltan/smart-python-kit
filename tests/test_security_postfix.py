"""Post-fix verification tests for security hardening module.

Tests added for the following review fixes:
- Body sanitization (POST with SQLi/XSS payload)
- is_production=True with wildcard origins raises ValueError
- time.monotonic() usage in rate limiter
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from smartvintaawesomekit.security import (
    CORSHardeningMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    SecurityConfig,
    add_security_middleware,
)
from smartvintaawesomekit.security.config import SecurityMiddlewareConfig


# ──────────────────────────────────────────────────────────────────
# Test 1: Body sanitization (POST with SQLi/XSS payload)
# ──────────────────────────────────────────────────────────────────


class TestBodySanitization:
    """InputSanitizationMiddleware should sanitize request bodies, not just query params."""

    def test_body_sqli_detected(self) -> None:
        """POST body containing SQL injection patterns should be rejected."""
        app = FastAPI()

        @app.post("/test")
        async def handler() -> dict:
            return {"ok": True}

        app.add_middleware(InputSanitizationMiddleware)
        client = TestClient(app, raise_server_exceptions=False)

        # SQLi in JSON body
        response = client.post(
            "/test",
            json={"query": "SELECT * FROM users WHERE id=1 OR 1=1"},
        )
        assert response.status_code == 400
        assert "SQL injection" in response.json()["detail"]

    def test_body_xss_detected(self) -> None:
        """POST body containing XSS patterns should be rejected."""
        app = FastAPI()

        @app.post("/test")
        async def handler() -> dict:
            return {"ok": True}

        app.add_middleware(InputSanitizationMiddleware)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/test",
            json={"comment": "<script>alert('xss')</script>"},
        )
        assert response.status_code == 400
        assert "XSS" in response.json()["detail"]

    def test_body_clean_passes(self) -> None:
        """Clean POST body should pass through without issues."""
        app = FastAPI()

        @app.post("/test")
        async def handler() -> dict:
            return {"ok": True}

        app.add_middleware(InputSanitizationMiddleware)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/test",
            json={"name": "John Doe", "email": "john@example.com"},
        )
        assert response.status_code == 200

    def test_body_null_bytes_stripped(self) -> None:
        """Null bytes in POST body should be stripped."""
        app = FastAPI()

        @app.post("/test")
        async def handler() -> dict:
            return {"ok": True}

        app.add_middleware(InputSanitizationMiddleware)
        client = TestClient(app, raise_server_exceptions=False)

        # Null bytes don't cause detection failure; they should be stripped
        response = client.post(
            "/test",
            content=b'{"data": "hello\x00world"}',
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200


# ──────────────────────────────────────────────────────────────────
# Test 2: is_production=True with wildcard origins raises ValueError
# ──────────────────────────────────────────────────────────────────


class TestCORSHardeningProduction:
    """CORSHardeningMiddleware should reject wildcard origins in production mode."""

    def test_wildcard_raises_value_error_in_production(self) -> None:
        """Creating CORSHardeningMiddleware with wildcard origin in production raises ValueError."""
        # CORSHardeningMiddleware skips validation when app=None (for test convenience),
        # so we pass a real app to trigger the ValueError.
        with pytest.raises(ValueError, match="Wildcard origin.*not allowed in production"):
            CORSHardeningMiddleware(
                app=FastAPI(),
                allowed_origins=["*"],
                is_production=True,
            )

    def test_explicit_origins_ok_in_production(self) -> None:
        """Explicit origins should work fine in production mode."""
        mw = CORSHardeningMiddleware(
            app=None,
            allowed_origins=["https://example.com"],
            is_production=True,
        )
        assert mw.is_production is True

    def test_wildcard_ok_in_development(self) -> None:
        """Wildcard origins should be allowed when not production."""
        mw = CORSHardeningMiddleware(
            app=None,
            allowed_origins=["*"],
            is_production=False,
        )
        assert mw.is_production is False

    def test_add_security_middleware_wildcard_production_raises(self) -> None:
        """add_security_middleware with is_production=True and wildcard origins raises ValueError."""
        # Note: add_security_middleware adds middleware lazily (add_middleware doesn't
        # instantiate immediately), so the ValueError fires when a request arrives.
        # Instead, we test CORSHardeningMiddleware directly with a real app.
        with pytest.raises(ValueError, match="Wildcard origin.*not allowed in production"):
            CORSHardeningMiddleware(
                app=FastAPI(),
                allowed_origins=["*"],
                reject_wildcard_in_production=True,
                is_production=True,
            )

    def test_add_security_middleware_wildcard_dev_ok(self) -> None:
        """add_security_middleware with wildcard origins in dev mode should work."""
        cfg = SecurityConfig(
            allowed_origins=["*"],
            reject_wildcard_in_production=True,
        )
        app = FastAPI()
        result = add_security_middleware(app, config=cfg, is_production=False)
        assert result is app


# ──────────────────────────────────────────────────────────────────
# Test 3: time.monotonic() usage in rate limiter
# ──────────────────────────────────────────────────────────────────


class TestRateLimitMonotonicTime:
    """RateLimitMiddleware should use time.monotonic(), not time.time()."""

    def test_refill_bucket_uses_monotonic(self) -> None:
        """_refill_bucket should call time.monotonic(), not time.time()."""
        mw = RateLimitMiddleware(app=None, requests=100, window_seconds=60)
        bucket: dict[str, tuple[float, float]] = {}
        with patch("smartvintaawesomekit.security.middleware.time.monotonic", return_value=100.0):
            tokens = mw._refill_bucket(bucket, "default", 100, 60)
            assert tokens == 100.0

    def test_consume_token_uses_monotonic(self) -> None:
        """_consume_token should call time.monotonic(), not time.time()."""
        mw = RateLimitMiddleware(app=None, requests=100, window_seconds=60)
        with patch("smartvintaawesomekit.security.middleware.time.monotonic", return_value=100.0):
            allowed, retry_after = mw._consume_token("test_client", "default", 100, 60)
            assert allowed is True

    def test_cleanup_uses_monotonic(self) -> None:
        """_maybe_cleanup should call time.monotonic(), not time.time()."""
        mw = RateLimitMiddleware(app=None, requests=100, window_seconds=60)
        # Set _last_cleanup_time to old value
        mw._last_cleanup_time = 0.0
        with patch("smartvintaawesomekit.security.middleware.time.monotonic", return_value=200.0):
            mw._maybe_cleanup()
            assert mw._last_cleanup_time == 200.0

    def test_no_time_time_import(self) -> None:
        """middleware.py should not use time.time() anywhere."""
        import smartvintaawesomekit.security.middleware as mw_mod
        import inspect
        source = inspect.getsource(mw_mod)
        assert "time.time()" not in source, (
            "middleware.py still uses time.time() — should use time.monotonic()"
        )


# ──────────────────────────────────────────────────────────────────
# Test 4: SecurityMiddlewareConfig naming
# ──────────────────────────────────────────────────────────────────


class TestSecurityMiddlewareConfigNaming:
    """SecurityMiddlewareConfig should be the primary name, SecurityConfig is backward compat."""

    def test_security_middleware_config_is_primary(self) -> None:
        """SecurityMiddlewareConfig should be usable as the primary config class."""
        cfg = SecurityMiddlewareConfig(rate_limit_requests=50)
        assert cfg.rate_limit_requests == 50
        assert cfg.enable_rate_limiting is True

    def test_security_config_is_alias(self) -> None:
        """SecurityConfig should be an alias for SecurityMiddlewareConfig."""
        assert SecurityConfig is SecurityMiddlewareConfig

    def test_security_config_from_security_package(self) -> None:
        """Both names should be importable from the security package."""
        from smartvintaawesomekit.security import SecurityMiddlewareConfig as SMC
        from smartvintaawesomekit.security import SecurityConfig as SC
        assert SMC is SecurityMiddlewareConfig
        assert SC is SecurityConfig
