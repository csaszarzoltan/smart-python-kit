"""ASGI middlewares for request tracing and metrics collection.

Both middlewares subclass :class:`starlette.middleware.base.BaseHTTPMiddleware`
so they can be attached with the standard ``app.add_middleware(...)`` API.
"""
from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware

from smartvintaawesomekit.observability.logging import _trace_id_var
from smartvintaawesomekit.observability.metrics import MetricsRegistry

logger = logging.getLogger("smartvintaawesomekit.observability.middleware")

#: Accepted X-Request-ID grammar: an alphanumeric start followed by up to 63
#: alphanumerics/hyphens (max 64 chars total). Values outside this grammar —
#: CRLF/control characters, spaces, markup, or over-length strings — are
#: rejected and replaced with a fresh UUID so inbound values are never echoed
#: or logged verbatim.
_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,63}")


def _normalize_request_id(value: str | None) -> str:
    """Return ``value`` when it conforms to the request-id grammar, else a fresh UUID hex.

    ``None`` (no inbound header) also yields a fresh UUID hex.
    """
    if value is None:
        return uuid.uuid4().hex
    if _REQUEST_ID_RE.fullmatch(value) is None:
        return uuid.uuid4().hex
    return value


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Accept or generate X-Request-ID, inject trace_id into logs, echo the header.

    For every request the middleware:

    - reuses the inbound ``X-Request-ID`` header value when it conforms to a
      bounded safe grammar (alphanumeric + hyphens, at most 64 chars);
      otherwise — or when the client sent none — generates a fresh UUID.
      Inbound values are never echoed or logged verbatim;
    - sets the request-scoped ``trace_id`` context variable so the JSON
      formatter attaches it to every log record emitted while the request is
      in flight;
    - emits a structured ``request completed`` log record;
    - echoes the accepted value back in the ``X-Request-ID`` response header.
    """

    def __init__(self, app: Any, header: str = "X-Request-ID") -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap.
            header: Request/response header carrying the request id.
        """
        super().__init__(app)
        self.header = header

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process one request: correlate, log, and echo the request id."""
        request_id = _normalize_request_id(request.headers.get(self.header))
        token = _trace_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            logger.info(
                "request completed",
                extra={
                    "trace_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
            _trace_id_var.reset(token)
        response.headers[self.header] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Count requests, record latency histograms, and error counters per route.

    A request is counted once it reaches the middleware; a route is identified
    by its route template (e.g. ``/users/{user_id}``) when the app defines one,
    falling back to the raw URL path otherwise — the registry's route cap
    bounds the number of distinct keys either way. Responses with
    ``status >= 500`` and exceptions raised downstream are both recorded as
    errors; exceptions are re-raised so the framework still produces the
    error response.
    """

    def __init__(self, app: Any, registry: MetricsRegistry | None = None) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap.
            registry: Optional shared :class:`MetricsRegistry`. A fresh one is
                created when omitted.
        """
        super().__init__(app)
        self.registry = registry or MetricsRegistry()

    def _route_key(self, path: str) -> str:
        """Map a concrete URL path to its route template to bound key cardinality.

        Walks the wrapped ASGI app chain (user middleware -> exception
        middleware -> router) to find the first object exposing ``routes``,
        then returns the template of the first matching route. Falls back to
        the raw path when no route matches (e.g. 404s on unknown paths); the
        registry's route cap bounds those keys.
        """
        container: Any = self.app
        for _ in range(8):  # bounded walk through the middleware stack
            routes = getattr(container, "routes", None)
            if routes is not None:
                for route in routes:
                    pattern = getattr(route, "path_regex", None)
                    if pattern is not None and pattern.fullmatch(path):
                        template = getattr(route, "path", None)
                        if isinstance(template, str):
                            return template
                return path
            container = getattr(container, "app", None)
            if container is None:
                break
        return path

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process one request: count it, time it, and record failures."""
        route = self._route_key(request.url.path)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            self.registry.increment_error_count(route)
            raise
        finally:
            self.registry.increment_request_count(route)
            self.registry.record_latency(route, time.perf_counter() - started)
        if response.status_code >= 500:
            self.registry.increment_error_count(route)
        return response
