"""Security configuration — validated, environment-aware config for security hardening."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SecurityMiddlewareConfig:
    """Runtime configuration for the security middleware module.

    Attributes:
        enable_rate_limiting: Enable token-bucket rate limiting (default: True).
        enable_security_headers: Enable security headers middleware (default: True).
        enable_cors_hardening: Enable CORS hardening middleware (default: True).
        enable_request_size_limit: Enable request size limiting (default: True).
        enable_input_sanitization: Enable input sanitization middleware (default: True).

        # Rate limiting config
        rate_limit_requests: Max requests per window (default: 100).
        rate_limit_window_seconds: Time window in seconds (default: 60).
        rate_limit_per_route: Dict of route -> (requests, window) for per-route limits.

        # Security headers config
        hsts_max_age: HSTS max-age in seconds (default: 31536000).
        hsts_include_subdomains: Include subdomains in HSTS (default: True).
        hsts_preload: HSTS preload flag (default: False).
        csp_policy: Content-Security-Policy value (default: "default-src 'self'").
        frame_options: X-Frame-Options value (default: "DENY").
        content_type_options: X-Content-Type-Options value (default: "nosniff").
        xss_protection: X-XSS-Protection value (default: "1; mode=block").
        referrer_policy: Referrer-Policy value (default: "strict-origin-when-cross-origin").

        # CORS hardening config
        allowed_origins: List of allowed origins (default: ["*"]).
        allowed_methods: List of allowed methods (default: ["*"]).
        allowed_headers: List of allowed headers (default: ["*"]).
        allow_credentials: Allow credentials (default: True).
        reject_wildcard_in_production: Reject wildcard origin in production (default: True).

        # Request size config
        max_body_size: Max request body size in bytes (default: 1048576 = 1MB).
        max_body_size_exceeded_message: Error message for 413 responses.

        # Input sanitization config
        strip_null_bytes: Strip null bytes from input (default: True).
        detect_sql_injection: Detect SQL injection patterns (default: True).
        detect_xss: Detect XSS patterns (default: True).
        sql_injection_patterns: Additional SQL injection regex patterns.
        xss_patterns: Additional XSS regex patterns.
    """

    # Feature toggles
    enable_rate_limiting: bool = True
    enable_security_headers: bool = True
    enable_cors_hardening: bool = True
    enable_request_size_limit: bool = True
    enable_input_sanitization: bool = True

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_per_route: dict[str, tuple[int, int]] | None = None

    # Security headers
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    csp_policy: str = "default-src 'self'"
    frame_options: str = "DENY"
    content_type_options: str = "nosniff"
    xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"

    # CORS hardening
    allowed_origins: list[str] | None = None
    allowed_methods: list[str] | None = None
    allowed_headers: list[str] | None = None
    allow_credentials: bool = True
    reject_wildcard_in_production: bool = True

    # Request size
    max_body_size: int = 1048576
    max_body_size_exceeded_message: str = "Request body exceeds maximum allowed size"

    # Input sanitization
    strip_null_bytes: bool = True
    detect_sql_injection: bool = True
    detect_xss: bool = True
    sql_injection_patterns: list[str] | None = None
    xss_patterns: list[str] | None = None

    def __post_init__(self) -> None:
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]
        if self.allowed_methods is None:
            self.allowed_methods = ["*"]
        if self.allowed_headers is None:
            self.allowed_headers = ["*"]
        if self.rate_limit_per_route is None:
            self.rate_limit_per_route = {}
        if self.sql_injection_patterns is None:
            self.sql_injection_patterns = []
        if self.xss_patterns is None:
            self.xss_patterns = []


# Backward compatibility alias - use SecurityMiddlewareConfig as primary name
SecurityConfig = SecurityMiddlewareConfig
