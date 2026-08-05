"""Observability orchestration — one-line FastAPI integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smartvintaawesomekit.observability.middleware import (
    MetricsMiddleware,
    RequestTracingMiddleware,
)
from smartvintaawesomekit.observability.otlp import configure_otlp_exporter


@dataclass
class ObservabilityConfig:
    """Runtime configuration for the observability module.

    Attributes:
        enable_tracing: Attach :class:`RequestTracingMiddleware` (default: True).
        enable_metrics: Attach :class:`MetricsMiddleware` (default: True).
        enable_otlp: Opt into OTLP export (default: False — requires the
            ``opentelemetry`` extra to actually export).
        service_name: Service name used for OTLP resource attributes.
        log_level: Log level string used by :func:`setup_logging`.
    """

    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_otlp: bool = False
    service_name: str = "smartvintaawesomekit"
    log_level: str = "INFO"


def install_observability(app: Any, config: ObservabilityConfig | None = None) -> Any:
    """Attach request tracing and metrics middleware to a FastAPI app.

    Middlewares are attached with the standard ``app.add_middleware(...)``
    API, so the app keeps its existing route handling untouched. When
    ``config.enable_otlp`` is set, the OTLP exporter is opted in as well.

    Returns the same app instance so integration stays one line:
    ``app = install_observability(app)``.

    Args:
        app: The FastAPI/Starlette application to instrument.
        config: Optional :class:`ObservabilityConfig`. Defaults to tracing and
            metrics enabled, OTLP disabled.

    Returns:
        The same ``app`` instance.
    """
    cfg = config or ObservabilityConfig()
    if cfg.enable_tracing:
        app.add_middleware(RequestTracingMiddleware)
    if cfg.enable_metrics:
        app.add_middleware(MetricsMiddleware)
    if cfg.enable_otlp:
        configure_otlp_exporter(service_name=cfg.service_name, enabled=True)
    return app
