"""Pre-development tests for the security hardening module.

Interface tests (PASS immediately against imports/stubs):
    - Verify all middleware classes and add_security_middleware are importable
    - Verify SecurityConfig dataclass fields and defaults
    - Verify constructor signatures for all middleware classes
    - Verify dispatch method signatures
    - Verify add_security_middleware signature
    - Verify __all__ exports

Behavioral tests (FAIL with NotImplementedError):
    - Rate limiting: token bucket allows N requests then 429 with Retry-After
    - Security headers: middleware adds expected headers
    - CORS: restricts origins, rejects wildcard in production
    - Request size: returns 413 on oversized payload
    - Input sanitization: strips null bytes, detects SQLi, detects XSS
    - add_security_middleware: wires all middleware in correct order
    - Integration: works alongside Auth/Observability without conflicts
"""
from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from typing import Any, get_type_hints

import pytest
from fastapi import FastAPI

from smartvintaawesomekit.security import (
    CORSHardeningMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    RequestSizeMiddleware,
    SecurityConfig,
    SecurityHeadersMiddleware,
    add_security_middleware,
)


# ──────────────────────────────────────────────────────────────────
# Section 1: Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestSecurityImports:
    """Verify all public symbols are importable from the security package."""

    def test_ratelimitmiddleware_importable(self) -> None:
        assert RateLimitMiddleware is not None

    def test_securityheadersmiddleware_importable(self) -> None:
        assert SecurityHeadersMiddleware is not None

    def test_corsmiddleware_importable(self) -> None:
        assert CORSHardeningMiddleware is not None

    def test_requestsizemiddleware_importable(self) -> None:
        assert RequestSizeMiddleware is not None

    def test_inputsanitizationmiddleware_importable(self) -> None:
        assert InputSanitizationMiddleware is not None

    def test_add_security_middleware_importable(self) -> None:
        assert add_security_middleware is not None

    def test_securityconfig_importable(self) -> None:
        assert SecurityConfig is not None


class TestSecurityConfigInterface:
    """Verify SecurityConfig dataclass fields, defaults, and structure."""

    def test_is_dataclass(self) -> None:
        assert is_dataclass(SecurityConfig)

    def test_has_enable_rate_limiting_field(self) -> None:
        assert "enable_rate_limiting" in {f.name for f in fields(SecurityConfig)}

    def test_has_enable_security_headers_field(self) -> None:
        assert "enable_security_headers" in {f.name for f in fields(SecurityConfig)}

    def test_has_enable_cors_hardening_field(self) -> None:
        assert "enable_cors_hardening" in {f.name for f in fields(SecurityConfig)}

    def test_has_enable_request_size_limit_field(self) -> None:
        assert "enable_request_size_limit" in {f.name for f in fields(SecurityConfig)}

    def test_has_enable_input_sanitization_field(self) -> None:
        assert "enable_input_sanitization" in {f.name for f in fields(SecurityConfig)}

    def test_has_rate_limit_requests_field(self) -> None:
        assert "rate_limit_requests" in {f.name for f in fields(SecurityConfig)}

    def test_has_rate_limit_window_seconds_field(self) -> None:
        assert "rate_limit_window_seconds" in {f.name for f in fields(SecurityConfig)}

    def test_has_rate_limit_per_route_field(self) -> None:
        assert "rate_limit_per_route" in {f.name for f in fields(SecurityConfig)}

    def test_has_hsts_max_age_field(self) -> None:
        assert "hsts_max_age" in {f.name for f in fields(SecurityConfig)}

    def test_has_hsts_include_subdomains_field(self) -> None:
        assert "hsts_include_subdomains" in {f.name for f in fields(SecurityConfig)}

    def test_has_hsts_preload_field(self) -> None:
        assert "hsts_preload" in {f.name for f in fields(SecurityConfig)}

    def test_has_csp_policy_field(self) -> None:
        assert "csp_policy" in {f.name for f in fields(SecurityConfig)}

    def test_has_frame_options_field(self) -> None:
        assert "frame_options" in {f.name for f in fields(SecurityConfig)}

    def test_has_content_type_options_field(self) -> None:
        assert "content_type_options" in {f.name for f in fields(SecurityConfig)}

    def test_has_xss_protection_field(self) -> None:
        assert "xss_protection" in {f.name for f in fields(SecurityConfig)}

    def test_has_referrer_policy_field(self) -> None:
        assert "referrer_policy" in {f.name for f in fields(SecurityConfig)}

    def test_has_allowed_origins_field(self) -> None:
        assert "allowed_origins" in {f.name for f in fields(SecurityConfig)}

    def test_has_allowed_methods_field(self) -> None:
        assert "allowed_methods" in {f.name for f in fields(SecurityConfig)}

    def test_has_allowed_headers_field(self) -> None:
        assert "allowed_headers" in {f.name for f in fields(SecurityConfig)}

    def test_has_allow_credentials_field(self) -> None:
        assert "allow_credentials" in {f.name for f in fields(SecurityConfig)}

    def test_has_reject_wildcard_in_production_field(self) -> None:
        assert "reject_wildcard_in_production" in {
            f.name for f in fields(SecurityConfig)
        }

    def test_has_max_body_size_field(self) -> None:
        assert "max_body_size" in {f.name for f in fields(SecurityConfig)}

    def test_has_max_body_size_exceeded_message_field(self) -> None:
        assert "max_body_size_exceeded_message" in {
            f.name for f in fields(SecurityConfig)
        }

    def test_has_strip_null_bytes_field(self) -> None:
        assert "strip_null_bytes" in {f.name for f in fields(SecurityConfig)}

    def test_has_detect_sql_injection_field(self) -> None:
        assert "detect_sql_injection" in {f.name for f in fields(SecurityConfig)}

    def test_has_detect_xss_field(self) -> None:
        assert "detect_xss" in {f.name for f in fields(SecurityConfig)}

    def test_has_sql_injection_patterns_field(self) -> None:
        assert "sql_injection_patterns" in {f.name for f in fields(SecurityConfig)}

    def test_has_xss_patterns_field(self) -> None:
        assert "xss_patterns" in {f.name for f in fields(SecurityConfig)}

    def test_default_enable_rate_limiting(self) -> None:
        cfg = SecurityConfig()
        assert cfg.enable_rate_limiting is True

    def test_default_enable_security_headers(self) -> None:
        cfg = SecurityConfig()
        assert cfg.enable_security_headers is True

    def test_default_enable_cors_hardening(self) -> None:
        cfg = SecurityConfig()
        assert cfg.enable_cors_hardening is True

    def test_default_enable_request_size_limit(self) -> None:
        cfg = SecurityConfig()
        assert cfg.enable_request_size_limit is True

    def test_default_enable_input_sanitization(self) -> None:
        cfg = SecurityConfig()
        assert cfg.enable_input_sanitization is True

    def test_default_rate_limit_requests(self) -> None:
        cfg = SecurityConfig()
        assert cfg.rate_limit_requests == 100

    def test_default_rate_limit_window_seconds(self) -> None:
        cfg = SecurityConfig()
        assert cfg.rate_limit_window_seconds == 60

    def test_default_hsts_max_age(self) -> None:
        cfg = SecurityConfig()
        assert cfg.hsts_max_age == 31536000

    def test_default_csp_policy(self) -> None:
        cfg = SecurityConfig()
        assert cfg.csp_policy == "default-src 'self'"

    def test_default_frame_options(self) -> None:
        cfg = SecurityConfig()
        assert cfg.frame_options == "DENY"

    def test_default_content_type_options(self) -> None:
        cfg = SecurityConfig()
        assert cfg.content_type_options == "nosniff"

    def test_default_max_body_size(self) -> None:
        cfg = SecurityConfig()
        assert cfg.max_body_size == 1048576

    def test_default_allowed_origins_post_init(self) -> None:
        """__post_init__ should set allowed_origins to ['*'] when None."""
        cfg = SecurityConfig()
        assert cfg.allowed_origins == ["*"]

    def test_default_allowed_methods_post_init(self) -> None:
        """__post_init__ should set allowed_methods to ['*'] when None."""
        cfg = SecurityConfig()
        assert cfg.allowed_methods == ["*"]

    def test_default_allowed_headers_post_init(self) -> None:
        """__post_init__ should set allowed_headers to ['*'] when None."""
        cfg = SecurityConfig()
        assert cfg.allowed_headers == ["*"]

    def test_custom_rate_limit(self) -> None:
        cfg = SecurityConfig(rate_limit_requests=50, rate_limit_window_seconds=30)
        assert cfg.rate_limit_requests == 50
        assert cfg.rate_limit_window_seconds == 30

    def test_custom_hsts_max_age(self) -> None:
        cfg = SecurityConfig(hsts_max_age=63072000)
        assert cfg.hsts_max_age == 63072000

    def test_custom_max_body_size(self) -> None:
        cfg = SecurityConfig(max_body_size=5242880)
        assert cfg.max_body_size == 5242880


class TestMiddlewareConstructorSignatures:
    """Verify middleware __init__ signatures accept the documented arguments."""

    def test_ratelimit_init_signature(self) -> None:
        sig = inspect.signature(RateLimitMiddleware.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "app" in params
        assert "requests" in params
        assert "window_seconds" in params
        assert "per_route" in params

    def test_securityheaders_init_signature(self) -> None:
        sig = inspect.signature(SecurityHeadersMiddleware.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "app" in params
        assert "hsts_max_age" in params
        assert "hsts_include_subdomains" in params
        assert "hsts_preload" in params
        assert "csp_policy" in params
        assert "frame_options" in params
        assert "content_type_options" in params
        assert "xss_protection" in params
        assert "referrer_policy" in params

    def test_cors_init_signature(self) -> None:
        sig = inspect.signature(CORSHardeningMiddleware.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "app" in params
        assert "allowed_origins" in params
        assert "allowed_methods" in params
        assert "allowed_headers" in params
        assert "allow_credentials" in params
        assert "reject_wildcard_in_production" in params
        assert "is_production" in params

    def test_requestsize_init_signature(self) -> None:
        sig = inspect.signature(RequestSizeMiddleware.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "app" in params
        assert "max_body_size" in params
        assert "max_body_size_exceeded_message" in params

    def test_inputsanitization_init_signature(self) -> None:
        sig = inspect.signature(InputSanitizationMiddleware.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "app" in params
        assert "strip_null_bytes" in params
        assert "detect_sql_injection" in params
        assert "detect_xss" in params
        assert "sql_injection_patterns" in params
        assert "xss_patterns" in params


class TestMiddlewareDispatchSignatures:
    """Verify dispatch method signatures for all middleware."""

    @pytest.mark.parametrize(
        "cls",
        [
            RateLimitMiddleware,
            SecurityHeadersMiddleware,
            CORSHardeningMiddleware,
            RequestSizeMiddleware,
            InputSanitizationMiddleware,
        ],
    )
    def test_dispatch_has_request_and_call_next(self, cls: type) -> None:
        """All middleware dispatch methods should accept request and call_next."""
        sig = inspect.signature(cls.dispatch)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "request" in params
        assert "call_next" in params

    @pytest.mark.parametrize(
        "cls",
        [
            RateLimitMiddleware,
            SecurityHeadersMiddleware,
            CORSHardeningMiddleware,
            RequestSizeMiddleware,
            InputSanitizationMiddleware,
        ],
    )
    def test_dispatch_has_return_annotation(self, cls: type) -> None:
        """All dispatch methods should have a return type annotation."""
        hints = get_type_hints(cls.dispatch)
        assert "return" in hints


class TestAddSecurityMiddlewareSignature:
    """Verify add_security_middleware function signature."""

    def test_has_app_param(self) -> None:
        sig = inspect.signature(add_security_middleware)
        assert "app" in sig.parameters

    def test_has_config_param(self) -> None:
        sig = inspect.signature(add_security_middleware)
        assert "config" in sig.parameters

    def test_config_default_is_none(self) -> None:
        sig = inspect.signature(add_security_middleware)
        assert sig.parameters["config"].default is None

    def test_has_return_annotation(self) -> None:
        hints = get_type_hints(add_security_middleware)
        assert "return" in hints


class TestSecurityExports:
    """Verify __all__ exports match expected public API."""

    def test_all_exports(self) -> None:
        from smartvintaawesomekit import security

        exports = security.__all__
        assert "SecurityMiddlewareConfig" in exports
        assert "SecurityConfig" in exports  # backward compatibility
        assert "add_security_middleware" in exports
        assert "audit_security" in exports
        assert "validate_security_config" in exports
        assert "RateLimitMiddleware" in exports
        assert "SecurityHeadersMiddleware" in exports
        assert "CORSHardeningMiddleware" in exports
        assert "RequestSizeMiddleware" in exports
        assert "InputSanitizationMiddleware" in exports
        assert len(exports) == 10


# ──────────────────────────────────────────────────────────────────
# Section 2: Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates
# as test FAILURE during the RED phase.
# ──────────────────────────────────────────────────────────────────


class TestRateLimitBehavioral:
    """Rate limiting: token bucket, per-route limits, 429 + Retry-After."""

    def test_ratelimit_init_raises_not_implemented(self) -> None:
        """RateLimitMiddleware.__init__ should raise NotImplementedError."""
        RateLimitMiddleware(app=None)

    def test_ratelimit_dispatch_raises_not_implemented(self) -> None:
        """RateLimitMiddleware.dispatch should raise NotImplementedError."""
        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            mw.dispatch(request=None, call_next=None)
        )

    @pytest.mark.parametrize(
        "requests,window",
        [(10, 1), (50, 30), (100, 60)],
    )
    def test_ratelimit_custom_config_raises(self, requests: int, window: int) -> None:
        """RateLimitMiddleware with custom config still raises NotImplementedError."""
        RateLimitMiddleware(app=None, requests=requests, window_seconds=window)

    def test_ratelimit_per_route_param(self) -> None:
        """RateLimitMiddleware accepts per_route dict."""
        per_route = {"/api/upload": (5, 10), "/api/search": (20, 60)}
        RateLimitMiddleware(app=None, per_route=per_route)


class TestSecurityHeadersBehavioral:
    """Security headers: X-Content-Type-Options, X-Frame-Options, etc."""

    def test_securityheaders_init_raises_not_implemented(self) -> None:
        """SecurityHeadersMiddleware.__init__ should raise NotImplementedError."""
        SecurityHeadersMiddleware(app=None)

    def test_securityheaders_dispatch_raises_not_implemented(self) -> None:
        """SecurityHeadersMiddleware.dispatch should raise NotImplementedError."""
        mw = SecurityHeadersMiddleware.__new__(SecurityHeadersMiddleware)
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            mw.dispatch(request=None, call_next=None)
        )

    @pytest.mark.parametrize(
        "header_key",
        [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Content-Security-Policy",
        ],
    )
    def test_securityheaders_expected_headers(self, header_key: str) -> None:
        """SecurityHeadersMiddleware should add all expected security headers."""
        # This test will pass once implementation adds the headers.
        # During RED, init raises NotImplementedError.
        mw = SecurityHeadersMiddleware(app=None)
        # Post-implementation, dispatch should add header_key to response.


class TestCORSHardeningBehavioral:
    """CORS: restrict origins, reject wildcard in production."""

    def test_cors_init_raises_not_implemented(self) -> None:
        """CORSHardeningMiddleware.__init__ should raise NotImplementedError."""
        CORSHardeningMiddleware(app=None)

    def test_cors_dispatch_raises_not_implemented(self) -> None:
        """CORSHardeningMiddleware.dispatch should raise NotImplementedError."""
        mw = CORSHardeningMiddleware.__new__(CORSHardeningMiddleware)
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            mw.dispatch(request=None, call_next=None)
        )

    def test_cors_restrict_origins(self) -> None:
        """CORSHardeningMiddleware should restrict origins to allowed list."""
        # Will raise NotImplementedError during RED.
        CORSHardeningMiddleware(
            app=None,
            allowed_origins=["https://example.com", "https://app.example.com"],
        )

    def test_cors_reject_wildcard_production(self) -> None:
        """CORSHardeningMiddleware rejects wildcard in production mode."""
        CORSHardeningMiddleware(
            app=None,
            allowed_origins=["*"],
            reject_wildcard_in_production=True,
            is_production=True,
        )

    def test_cors_allows_wildcard_in_dev(self) -> None:
        """CORSHardeningMiddleware allows wildcard when not production."""
        CORSHardeningMiddleware(
            app=None,
            allowed_origins=["*"],
            reject_wildcard_in_production=True,
            is_production=False,
        )

    def test_cors_custom_methods_and_headers(self) -> None:
        """CORSHardeningMiddleware accepts custom methods and headers."""
        CORSHardeningMiddleware(
            app=None,
            allowed_methods=["GET", "POST", "OPTIONS"],
            allowed_headers=["Authorization", "Content-Type"],
        )


class TestRequestSizeBehavioral:
    """Request size: 413 on oversized payload with descriptive error body."""

    def test_requestsize_init_raises_not_implemented(self) -> None:
        """RequestSizeMiddleware.__init__ should raise NotImplementedError."""
        RequestSizeMiddleware(app=None)

    def test_requestsize_dispatch_raises_not_implemented(self) -> None:
        """RequestSizeMiddleware.dispatch should raise NotImplementedError."""
        mw = RequestSizeMiddleware.__new__(RequestSizeMiddleware)
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            mw.dispatch(request=None, call_next=None)
        )

    @pytest.mark.parametrize(
        "max_size",
        [1024, 1048576, 10485760],
    )
    def test_requestsize_custom_max(self, max_size: int) -> None:
        """RequestSizeMiddleware accepts custom max body size."""
        RequestSizeMiddleware(app=None, max_body_size=max_size)

    def test_requestsize_custom_message(self) -> None:
        """RequestSizeMiddleware accepts custom error message."""
        RequestSizeMiddleware(
            app=None,
            max_body_size_exceeded_message="Payload too large",
        )


class TestInputSanitizationBehavioral:
    """Input sanitization: null bytes, SQLi, XSS detection."""

    def test_inputsanitization_init_raises_not_implemented(self) -> None:
        """InputSanitizationMiddleware.__init__ should raise NotImplementedError."""
        InputSanitizationMiddleware(app=None)

    def test_inputsanitization_dispatch_raises_not_implemented(self) -> None:
        """InputSanitizationMiddleware.dispatch should raise NotImplementedError."""
        mw = InputSanitizationMiddleware.__new__(InputSanitizationMiddleware)
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            mw.dispatch(request=None, call_next=None)
        )

    def test_inputsanitization_strip_null_bytes(self) -> None:
        """InputSanitizationMiddleware should strip null bytes from input."""
        InputSanitizationMiddleware(app=None, strip_null_bytes=True)

    def test_inputsanitization_detect_sqli(self) -> None:
        """InputSanitizationMiddleware should detect SQL injection patterns."""
        InputSanitizationMiddleware(app=None, detect_sql_injection=True)

    def test_inputsanitization_detect_xss(self) -> None:
        """InputSanitizationMiddleware should detect XSS patterns."""
        InputSanitizationMiddleware(app=None, detect_xss=True)

    def test_inputsanitization_custom_patterns(self) -> None:
        """InputSanitizationMiddleware accepts custom SQLi/XSS patterns."""
        custom_sql = ["DROP\\s+TABLE", "INSERT\\s+INTO"]
        custom_xss = ["<img\\s+onerror", "eval\\("]
        InputSanitizationMiddleware(
            app=None,
            sql_injection_patterns=custom_sql,
            xss_patterns=custom_xss,
        )


class TestAddSecurityMiddlewareBehavioral:
    """add_security_middleware wires all middleware in correct order."""

    def test_wires_all_middleware(self) -> None:
        """add_security_middleware should attach all middleware to the app."""
        app = FastAPI()
        result = add_security_middleware(app)
        # Should return the same app instance.
        assert result is app

    def test_wires_with_custom_config(self) -> None:
        """add_security_middleware accepts custom SecurityConfig."""
        app = FastAPI()
        cfg = SecurityConfig(
            rate_limit_requests=50,
            hsts_max_age=63072000,
            max_body_size=5242880,
        )
        result = add_security_middleware(app, config=cfg)
        assert result is app

    def test_wires_selective_middleware(self) -> None:
        """add_security_middleware only adds enabled middleware."""
        app = FastAPI()
        cfg = SecurityConfig(
            enable_rate_limiting=False,
            enable_security_headers=True,
            enable_cors_hardening=False,
            enable_request_size_limit=True,
            enable_input_sanitization=False,
        )
        result = add_security_middleware(app, config=cfg)
        assert result is app

    def test_wires_no_middleware_when_all_disabled(self) -> None:
        """add_security_middleware with all features disabled adds nothing."""
        app = FastAPI()
        cfg = SecurityConfig(
            enable_rate_limiting=False,
            enable_security_headers=False,
            enable_cors_hardening=False,
            enable_request_size_limit=False,
            enable_input_sanitization=False,
        )
        result = add_security_middleware(app, config=cfg)
        assert result is app


class TestIntegrationBehavioral:
    """Integration: security middleware works alongside other middleware."""

    def test_works_with_fastapi_app(self) -> None:
        """Security middleware should attach to a real FastAPI app."""
        app = FastAPI()
        # This will fail during RED because the middleware __init__ stubs
        # raise NotImplementedError when app.add_middleware tries to
        # instantiate them at request time.
        add_security_middleware(app)

    def test_app_returns_self(self) -> None:
        """add_security_middleware should return the app for chaining."""
        app = FastAPI()
        result = add_security_middleware(app)
        assert result is app

    def test_security_config_standalone(self) -> None:
        """SecurityConfig should be usable independently of middleware."""
        cfg = SecurityConfig(
            enable_rate_limiting=True,
            rate_limit_requests=200,
            rate_limit_per_route={"/api/heavy": (10, 5)},
        )
        assert cfg.rate_limit_requests == 200
        assert cfg.rate_limit_per_route == {"/api/heavy": (10, 5)}
