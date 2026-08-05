"""Observability module — structured logging, request tracing, and metrics.

Public API:
- ``setup_logging()``: enable structured JSON logging (zero-config fallback).
- ``install_observability(app)``: one-line FastAPI integration.
- ``RequestTracingMiddleware`` / ``MetricsMiddleware``: ASGI middlewares.
- ``MetricsRegistry``: in-process per-route metrics store.
- ``configure_otlp_exporter()`` / ``otlp_enabled()``: optional OTLP export
  (opentelemetry extra, disabled by default — no import-time dependency).
"""
from __future__ import annotations

from smartvintaawesomekit.observability.core import ObservabilityConfig, install_observability
from smartvintaawesomekit.observability.logging import LoggingConfig, setup_logging
from smartvintaawesomekit.observability.metrics import MetricsRegistry
from smartvintaawesomekit.observability.middleware import (
    MetricsMiddleware,
    RequestTracingMiddleware,
)
from smartvintaawesomekit.observability.otlp import configure_otlp_exporter, otlp_enabled

__all__ = [
    "LoggingConfig",
    "MetricsMiddleware",
    "MetricsRegistry",
    "ObservabilityConfig",
    "RequestTracingMiddleware",
    "configure_otlp_exporter",
    "install_observability",
    "otlp_enabled",
    "setup_logging",
]
