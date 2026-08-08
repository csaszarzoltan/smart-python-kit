"""Security hardening module — rate limiting, security headers,
CORS hardening, request size limits, input sanitization.

Public API:
- ``add_security_middleware(app, config)``: one-line FastAPI integration
  for all security middleware.
- ``SecurityConfig``: runtime configuration for the security module.
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

from smartvintaawesomekit.security.config import SecurityConfig
from smartvintaawesomekit.security.core import add_security_middleware
from smartvintaawesomekit.security.middleware import (
    CORSHardeningMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    RequestSizeMiddleware,
    SecurityHeadersMiddleware,
)

__all__ = [
    "SecurityConfig",
    "add_security_middleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "CORSHardeningMiddleware",
    "RequestSizeMiddleware",
    "InputSanitizationMiddleware",
]
