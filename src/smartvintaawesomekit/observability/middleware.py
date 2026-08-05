"""ASGI middlewares for request tracing and metrics collection.

Both middlewares subclass :class:`starlette.middleware.base.BaseHTTPMiddleware`
so they can be attached with the standard ``app.add_middleware(...)`` API.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware

from smartvintaawesomekit.observability.logging import _trace_id_var
from smartvintaawesomekit.observability.metrics import MetricsRegistry

logger = logging.getLogger("smartvintaawesomekit.observability.middleware")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Accept or generate X-Request-ID, inject trace_id into logs, echo the header.

    For every request the middleware:

    - reuses the inbound ``X-Request-ID`` header value, or generates a UUID
      when the client did not send one;
    - sets the request-scoped ``trace_id`` context variable so the JSON
      formatter attaches it to every log record emitted while the request is
      in flight;
    - emits a structured ``request completed`` log record;
    - echoes the value back in the ``X-Request-ID`` response header.
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
        request_id = request.headers.get(self.header) or uuid.uuid4().hex
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
    by its URL path. Exceptions raised downstream are recorded as errors and
    re-raised so the framework still produces the error response.
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

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Process one request: count it, time it, and record failures."""
        route = request.url.path
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            self.registry.increment_error_count(route)
            raise
        finally:
            self.registry.increment_request_count(route)
            self.registry.record_latency(route, time.perf_counter() - started)
        return response
