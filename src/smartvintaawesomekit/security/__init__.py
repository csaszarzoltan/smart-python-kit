"""Security hardening module — rate limiting, security headers,
CORS hardening, request size limits, input sanitization.

Public API:
- ``add_security_middleware(app, config)``: one-line FastAPI integration
  for all security middleware.
- ``audit_security(config, environment)``: run a security audit and return
  a structured report.
- ``validate_security_config(...)``: validate security settings compatibility.
- ``SecurityMiddlewareConfig``: runtime configuration for the security module.
- ``RateLimitMiddleware``: token-bucket rate limiting with
  per-route/client limits.
- ``SecurityHeadersMiddleware``: adds security headers (HSTS, CSP,
  X-Frame, etc.).
- ``CORSHardeningMiddleware``: validates and restricts CORS origins.
- ``RequestSizeMiddleware``: configurable max body size with 413 on
  oversized payloads.
- ``InputSanitizationMiddleware``: strips null bytes, detects
  SQLi/XSS patterns.
"""

from __future__ import annotations

from smartvintaawesomekit.security.config import (
    SecurityConfig,  # backward compatibility
    SecurityMiddlewareConfig,
)
from smartvintaawesomekit.security.core import (
    add_security_middleware,
    audit_security,
    validate_security_config,
)
from smartvintaawesomekit.security.middleware import (
    CORSHardeningMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    RequestSizeMiddleware,
    SecurityHeadersMiddleware,
)

__all__ = [
    "SecurityMiddlewareConfig",
    "SecurityConfig",  # backward compatibility
    "add_security_middleware",
    "audit_security",
    "validate_security_config",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "CORSHardeningMiddleware",
    "RequestSizeMiddleware",
    "InputSanitizationMiddleware",
]
