"""Security orchestration — one-line FastAPI integration for all security middleware."""

from __future__ import annotations

from typing import Any

from smartvintaawesomekit.security.config import SecurityConfig
from smartvintaawesomekit.security.middleware import (
    CORSHardeningMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    RequestSizeMiddleware,
    SecurityHeadersMiddleware,
)


def add_security_middleware(  # noqa: ANN401
    app: Any, config: SecurityConfig | None = None  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Attach all security middleware to a FastAPI app in the correct order.

    Middleware order (outermost first, innermost last):
    1. CORSHardeningMiddleware — validate CORS early
    2. RateLimitMiddleware — rate limit before processing
    3. RequestSizeMiddleware — check body size early
    4. InputSanitizationMiddleware — sanitize input
    5. SecurityHeadersMiddleware — add security headers to response

    Args:
        app: The FastAPI/Starlette application to instrument.
        config: Optional :class:`SecurityConfig`. Defaults to all features enabled.

    Returns:
        The same ``app`` instance.
    """
    cfg = config or SecurityConfig()

    # Order matters: outermost middleware wraps the response, so apply in reverse
    # of the logical request flow. The last added is the innermost (closest to handler).

    if cfg.enable_security_headers:
        app.add_middleware(
            SecurityHeadersMiddleware,
            hsts_max_age=cfg.hsts_max_age,
            hsts_include_subdomains=cfg.hsts_include_subdomains,
            hsts_preload=cfg.hsts_preload,
            csp_policy=cfg.csp_policy,
            frame_options=cfg.frame_options,
            content_type_options=cfg.content_type_options,
            xss_protection=cfg.xss_protection,
            referrer_policy=cfg.referrer_policy,
        )

    if cfg.enable_input_sanitization:
        app.add_middleware(
            InputSanitizationMiddleware,
            strip_null_bytes=cfg.strip_null_bytes,
            detect_sql_injection=cfg.detect_sql_injection,
            detect_xss=cfg.detect_xss,
            sql_injection_patterns=cfg.sql_injection_patterns,
            xss_patterns=cfg.xss_patterns,
        )

    if cfg.enable_request_size_limit:
        app.add_middleware(
            RequestSizeMiddleware,
            max_body_size=cfg.max_body_size,
            max_body_size_exceeded_message=cfg.max_body_size_exceeded_message,
        )

    if cfg.enable_rate_limiting:
        app.add_middleware(
            RateLimitMiddleware,
            requests=cfg.rate_limit_requests,
            window_seconds=cfg.rate_limit_window_seconds,
            per_route=cfg.rate_limit_per_route,
        )

    if cfg.enable_cors_hardening:
        app.add_middleware(
            CORSHardeningMiddleware,
            allowed_origins=cfg.allowed_origins,
            allowed_methods=cfg.allowed_methods,
            allowed_headers=cfg.allowed_headers,
            allow_credentials=cfg.allow_credentials,
            reject_wildcard_in_production=cfg.reject_wildcard_in_production,
            is_production=False,  # Will be set from Settings
        )

    return app
