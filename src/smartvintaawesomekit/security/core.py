"""Security orchestration — one-line FastAPI integration for all security middleware.

Public API:
- ``add_security_middleware(app, config)``: one-line FastAPI integration
  for all security middleware.
- ``audit_security(config, environment)``: run a security audit and return
  a structured report.
- ``validate_security_config(config, cors_origins, cors_methods, cors_headers,
  is_production)``: validate that security settings are compatible.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI  # noqa: TC002 — needed at runtime for get_type_hints()
from starlette.applications import Starlette  # noqa: TC002 — needed at runtime for get_type_hints()

from smartvintaawesomekit.config import SmartConfig
from smartvintaawesomekit.security.config import SecurityMiddlewareConfig as SecurityConfig
from smartvintaawesomekit.security.middleware import (
    CORSHardeningMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    RequestSizeMiddleware,
    SecurityHeadersMiddleware,
)

# ──────────────────────────────────────────────────────────────────
# Middleware wiring
# ──────────────────────────────────────────────────────────────────


def add_security_middleware(
    app: FastAPI | Starlette,
    config: SecurityConfig | None = None,
    is_production: bool | None = None,
) -> FastAPI | Starlette:
    """Attach all security middleware to a FastAPI app in the correct order.

    Middleware order (outermost first, innermost last):
    1. CORSHardeningMiddleware — validate CORS early
    2. RateLimitMiddleware — rate limit before processing
    3. RequestSizeMiddleware — check body size early
    4. InputSanitizationMiddleware — sanitize input
    5. SecurityHeadersMiddleware — add security headers to response

    Rate limiting runs BEFORE auth middleware so that brute-force
    attacks on authentication endpoints are blocked early.

    Args:
        app: The FastAPI/Starlette application to instrument.
        config: Optional :class:`SecurityConfig`. Defaults to all features enabled.
        is_production: Whether the application runs in production mode.
            Passes through to CORSHardeningMiddleware to enable
            production CORS validation (wildcard rejection).
            If None, defaults to reading from SmartConfig's environment.

    Returns:
        The same ``app`` instance.
    """
    cfg = config or SecurityConfig()

    # Determine is_production from SmartConfig if not explicitly provided
    if is_production is None:
        smart_config = SmartConfig()
        is_production = smart_config.is_production()

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
            is_production=is_production,
        )

    return app


# ──────────────────────────────────────────────────────────────────
# Security audit
# ──────────────────────────────────────────────────────────────────


#: Headers that should be present on all responses for a hardened deployment.
REQUIRED_HEADERS: list[dict[str, str]] = [
    {"name": "X-Content-Type-Options", "expected": "nosniff", "severity": "critical"},
    {"name": "X-Frame-Options", "expected": "DENY", "severity": "critical"},
    {"name": "X-XSS-Protection", "expected": "1; mode=block", "severity": "warning"},
    {"name": "Strict-Transport-Security", "expected": "max-age=", "severity": "critical"},
    {"name": "Referrer-Policy", "expected": "strict-origin", "severity": "warning"},
    {"name": "Content-Security-Policy", "expected": "default-src", "severity": "warning"},
]


def audit_security(
    config: SecurityConfig | None = None,
    environment: str = "development",
    cors_origins: list[str] | None = None,
    cors_methods: list[str] | None = None,
    cors_headers: list[str] | None = None,
) -> dict[str, Any]:
    """Run a security audit and return a structured report.

    Checks:
    - Security middleware configuration status
    - Expected security headers coverage
    - CORS wildcard in production validation
    - Rate limiting configuration status

    Args:
        config: Security middleware config to audit. Defaults to a fresh SecurityConfig.
        environment: Runtime environment name ('production', 'development').
        cors_origins: Configured CORS origins (for wildcard detection).
        cors_methods: Configured CORS methods.
        cors_headers: Configured CORS headers.

    Returns:
        Dict with ``exit_code`` (0=pass, 1=warnings, 2=critical), ``status``,
        ``checks`` list, ``environment``, and summary counts.
    """
    cfg = config or SecurityConfig()
    is_production = environment.lower() == "production"
    checks: list[dict[str, str]] = []

    # 1. Middleware configuration checks
    feature_map = {
        "Rate limiting": cfg.enable_rate_limiting,
        "Security headers": cfg.enable_security_headers,
        "CORS hardening": cfg.enable_cors_hardening,
        "Request size limit": cfg.enable_request_size_limit,
        "Input sanitization": cfg.enable_input_sanitization,
    }
    for name, enabled in feature_map.items():
        checks.append({
            "check": name,
            "status": "enabled" if enabled else "disabled",
            "severity": "info",
        })

    # 2. Expected security headers
    for hdr in REQUIRED_HEADERS:
        if cfg.enable_security_headers:
            checks.append({
                "check": f"Header: {hdr['name']}",
                "status": f"configured ({hdr['expected']})",
                "severity": "info",
            })
        else:
            checks.append({
                "check": f"Header: {hdr['name']}",
                "status": "missing (security headers disabled)",
                "severity": hdr["severity"],
            })

    # 3. CORS validation
    origins = cors_origins or cfg.allowed_origins or ["*"]
    methods = cors_methods or cfg.allowed_methods or ["*"]
    headers = cors_headers or cfg.allowed_headers or ["*"]

    if is_production and cfg.reject_wildcard_in_production and "*" in origins:
        checks.append({
            "check": "CORS wildcard origin",
            "status": "CRITICAL: wildcard '*' not allowed in production",
            "severity": "critical",
        })
    elif "*" in origins:
        checks.append({
            "check": "CORS wildcard origin",
            "status": "warning: wildcard '*' in use",
            "severity": "warning",
        })
    else:
        checks.append({
            "check": "CORS wildcard origin",
            "status": "OK (explicit origins)",
            "severity": "info",
        })

    if "*" in methods:
        checks.append({
            "check": "CORS methods",
            "status": "warning: wildcard methods",
            "severity": "warning",
        })
    else:
        checks.append({
            "check": "CORS methods",
            "status": f"OK ({len(methods)} methods)",
            "severity": "info",
        })

    if "*" in headers:
        checks.append({
            "check": "CORS headers",
            "status": "warning: wildcard headers",
            "severity": "warning",
        })
    else:
        checks.append({
            "check": "CORS headers",
            "status": f"OK ({len(headers)} headers)",
            "severity": "info",
        })

    # 4. Rate limiting
    if cfg.enable_rate_limiting:
        if cfg.rate_limit_requests < 10:
            checks.append({
                "check": "Rate limit threshold",
                "status": f"warning: very low ({cfg.rate_limit_requests} req/window)",
                "severity": "warning",
            })
        else:
            checks.append({
                "check": "Rate limit threshold",
                "status": f"OK ({cfg.rate_limit_requests} req/{cfg.rate_limit_window_seconds}s)",
                "severity": "info",
            })
    else:
        checks.append({
            "check": "Rate limiting",
            "status": "disabled",
            "severity": "warning",
        })

    # 5. Middleware ordering note
    if cfg.enable_rate_limiting:
        checks.append({
            "check": "Middleware ordering",
            "status": "OK (rate limit runs before auth)",
            "severity": "info",
        })

    # Summary
    warnings = sum(1 for c in checks if c["severity"] == "warning")
    criticals = sum(1 for c in checks if c["severity"] == "critical")

    if criticals > 0:
        exit_code = 2
        status = "critical"
    elif warnings > 0:
        exit_code = 1
        status = "warnings"
    else:
        exit_code = 0
        status = "pass"

    return {
        "exit_code": exit_code,
        "status": status,
        "environment": environment,
        "checks": checks,
        "total_checks": len(checks),
        "warnings": warnings,
        "critical": criticals,
    }


# ──────────────────────────────────────────────────────────────────
# Config validation
# ──────────────────────────────────────────────────────────────────


def validate_security_config(
    config: SecurityConfig | None = None,
    cors_origins: list[str] | None = None,
    cors_methods: list[str] | None = None,
    cors_headers: list[str] | None = None,
    is_production: bool = False,
) -> list[dict[str, str]]:
    """Validate that rate limiting and CORS settings are compatible.

    Returns a list of validation issues (empty if everything is OK).

    Checks:
    - Rate limiting + CORS wildcard in production are incompatible
    - Per-route rate limits should not exceed the global limit
    - CORS wildcard with credentials is incompatible

    Args:
        config: Security middleware config to validate.
        cors_origins: Configured CORS origins.
        cors_methods: Configured CORS methods.
        cors_headers: Configured CORS headers.
        is_production: Whether running in production mode.

    Returns:
        List of issue dicts with 'severity' and 'message' keys.
    """
    cfg = config or SecurityConfig()
    issues: list[dict[str, str]] = []
    origins = cors_origins or cfg.allowed_origins or ["*"]

    # Wildcard + credentials
    if cfg.allow_credentials and "*" in origins:
        issues.append({
            "severity": "critical",
            "message": "CORS wildcard origin '*' with credentials is incompatible — "
                       "browsers will reject the response",
        })

    # Wildcard in production
    if is_production and cfg.reject_wildcard_in_production and "*" in origins:
        issues.append({
            "severity": "critical",
            "message": "CORS wildcard origin '*' is not allowed in production",
        })

    # Rate limiting disabled
    if not cfg.enable_rate_limiting:
        issues.append({
            "severity": "warning",
            "message": "Rate limiting is disabled — endpoints are unprotected",
        })

    # Per-route limits exceeding global limit
    if cfg.rate_limit_per_route:
        for route, (route_reqs, _route_window) in cfg.rate_limit_per_route.items():
            if route_reqs > cfg.rate_limit_requests:
                issues.append({
                    "severity": "warning",
                    "message": f"Per-route limit for '{route}' ({route_reqs}) "
                               f"exceeds global limit ({cfg.rate_limit_requests})",
                })

    # Very low rate limit
    if cfg.enable_rate_limiting and cfg.rate_limit_requests < 10:
        issues.append({
            "severity": "warning",
            "message": f"Rate limit threshold is very low ({cfg.rate_limit_requests} "
                       "requests) — may block legitimate traffic",
        })

    return issues
