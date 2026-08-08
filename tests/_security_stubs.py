"""Stub security middleware classes — raise NotImplementedError for RED phase.

Do NOT commit this file. It exists only so interface tests can import and verify
signatures while behavioral tests fail cleanly with NotImplementedError.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from smartvintaawesomekit.security.config import SecurityConfig


class RateLimitMiddleware:
    """Token-bucket rate limiting middleware with per-route/client limits."""

    def __init__(
        self,
        app: Any,
        requests: int = 100,
        window_seconds: int = 60,
        per_route: Optional[dict[str, tuple[int, int]]] = None,
    ) -> None:
        """Initialize the rate limit middleware.

        Args:
            app: The ASGI application.
            requests: Max requests per window (default: 100).
            window_seconds: Time window in seconds (default: 60).
            per_route: Dict of route path -> (requests, window) for per-route limits.
        """
        raise NotImplementedError("RateLimitMiddleware is not implemented yet (RED phase)")

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process request — enforce rate limit, call next."""
        raise NotImplementedError(
            "RateLimitMiddleware.dispatch is not implemented yet (RED phase)"
        )


class SecurityHeadersMiddleware:
    """Adds security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: default-src 'self'
    """

    def __init__(
        self,
        app: Any,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        csp_policy: str = "default-src 'self'",
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
    ) -> None:
        """Initialize the security headers middleware."""
        raise NotImplementedError(
            "SecurityHeadersMiddleware is not implemented yet (RED phase)"
        )

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process request — add security headers to response."""
        raise NotImplementedError(
            "SecurityHeadersMiddleware.dispatch is not implemented yet (RED phase)"
        )


class CORSHardeningMiddleware:
    """Validates and restricts CORS origins; prevents wildcard in production mode.

    - Validates Origin header against allowed_origins
    - Rejects wildcard (*) origin when reject_wildcard_in_production is True
    - Returns appropriate CORS headers on preflight and actual requests
    """

    def __init__(
        self,
        app: Any,
        allowed_origins: Optional[list[str]] = None,
        allowed_methods: Optional[list[str]] = None,
        allowed_headers: Optional[list[str]] = None,
        allow_credentials: bool = True,
        reject_wildcard_in_production: bool = True,
        is_production: bool = False,
    ) -> None:
        """Initialize the CORS hardening middleware.

        Args:
            app: The ASGI application.
            allowed_origins: List of allowed origins (default: ["*"]).
            allowed_methods: List of allowed methods (default: ["*"]).
            allowed_headers: List of allowed headers (default: ["*"]).
            allow_credentials: Allow credentials (default: True).
            reject_wildcard_in_production: Reject wildcard in production (default: True).
            is_production: Whether running in production mode (default: False).
        """
        raise NotImplementedError(
            "CORSHardeningMiddleware is not implemented yet (RED phase)"
        )

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process request — validate CORS, add headers."""
        raise NotImplementedError(
            "CORSHardeningMiddleware.dispatch is not implemented yet (RED phase)"
        )


class RequestSizeMiddleware:
    """Configurable max body size middleware with 413 on oversized payloads.

    - Reads Content-Length header and/or streams body
    - Returns 413 with descriptive error body when limit exceeded
    """

    def __init__(
        self,
        app: Any,
        max_body_size: int = 1048576,
        max_body_size_exceeded_message: str = "Request body exceeds maximum allowed size",
    ) -> None:
        """Initialize the request size middleware.

        Args:
            app: The ASGI application.
            max_body_size: Max request body size in bytes (default: 1MB).
            max_body_size_exceeded_message: Error message for 413 responses.
        """
        raise NotImplementedError(
            "RequestSizeMiddleware is not implemented yet (RED phase)"
        )

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process request — check body size, call next."""
        raise NotImplementedError(
            "RequestSizeMiddleware.dispatch is not implemented yet (RED phase)"
        )


class InputSanitizationMiddleware:
    """Strips null bytes, detects SQL injection and XSS patterns in query params and body.

    - Strips null bytes from all input
    - Detects common SQL injection patterns (UNION, SELECT, DROP, etc.)
    - Detects XSS patterns (<script>, onerror=, javascript:, etc.)
    - Returns 400 with descriptive error on detection
    """

    def __init__(
        self,
        app: Any,
        strip_null_bytes: bool = True,
        detect_sql_injection: bool = True,
        detect_xss: bool = True,
        sql_injection_patterns: Optional[list[str]] = None,
        xss_patterns: Optional[list[str]] = None,
    ) -> None:
        """Initialize the input sanitization middleware.

        Args:
            app: The ASGI application.
            strip_null_bytes: Strip null bytes from input (default: True).
            detect_sql_injection: Detect SQL injection patterns (default: True).
            detect_xss: Detect XSS patterns (default: True).
            sql_injection_patterns: Additional SQL injection regex patterns.
            xss_patterns: Additional XSS regex patterns.
        """
        raise NotImplementedError(
            "InputSanitizationMiddleware is not implemented yet (RED phase)"
        )

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process request — sanitize input, call next."""
        raise NotImplementedError(
            "InputSanitizationMiddleware.dispatch is not implemented yet (RED phase)"
        )


def add_security_middleware(app: Any, config: SecurityConfig | None = None) -> Any:
    """Attach all security middleware to a FastAPI app in the correct order."""
    raise NotImplementedError("add_security_middleware is not implemented yet (RED phase)")