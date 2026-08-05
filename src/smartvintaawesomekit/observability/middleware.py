"""ASGI middlewares for request tracing and metrics collection."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from smartvintaawesomekit.observability.metrics import MetricsRegistry


class RequestTracingMiddleware:
    """Accept or generate X-Request-ID, inject trace_id into logs, echo the header."""

    def __init__(self, app: Any, header: str = "X-Request-ID") -> None:
        raise NotImplementedError("RequestTracingMiddleware is not implemented yet (RED phase)")

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        raise NotImplementedError(
            "RequestTracingMiddleware.dispatch is not implemented yet (RED phase)"
        )


class MetricsMiddleware:
    """Count requests, record latency histograms, and error counters per route."""

    def __init__(self, app: Any, registry: MetricsRegistry | None = None) -> None:
        raise NotImplementedError("MetricsMiddleware is not implemented yet (RED phase)")

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        raise NotImplementedError("MetricsMiddleware.dispatch is not implemented yet (RED phase)")
