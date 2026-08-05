"""Structured JSON logging setup for the observability module."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoggingConfig:
    """Configuration for structured logging."""

    json_format: bool = True
    level: str = "INFO"


def setup_logging(config: LoggingConfig | None = None) -> None:
    """Enable structured JSON logging on the root logger.

    Zero-config fallback: calling ``setup_logging()`` with no arguments must
    work out of the box (JSON output at INFO level).
    """
    raise NotImplementedError("setup_logging is not implemented yet (RED phase)")
