"""Observability orchestration — one-line FastAPI integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ObservabilityConfig:
    """Runtime configuration for the observability module."""

    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_otlp: bool = False
    service_name: str = "smartvintaawesomekit"
    log_level: str = "INFO"


def install_observability(app: Any, config: ObservabilityConfig | None = None) -> Any:
    """Attach request tracing and metrics middleware to a FastAPI app.

    Returns the same app instance so integration stays one line:
    ``app = install_observability(app)``.
    """
    raise NotImplementedError("install_observability is not implemented yet (RED phase)")
