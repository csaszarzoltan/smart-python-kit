"""Structured JSON logging setup for the observability module.

``setup_logging()`` installs a JSON formatter on the root logger so every
record — including records emitted by third-party libraries — becomes a
single-line JSON object. The formatter attaches the current request's
``trace_id`` (set by :class:`RequestTracingMiddleware`) to every record
emitted while a request is in flight, giving request-scoped correlation
without touching the emitting code.
"""
from __future__ import annotations

import contextvars
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

#: Current request trace id. Set by RequestTracingMiddleware while a request
#: is being processed; read by JsonFormatter so emitted records carry it.
_trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "smartvintaawesomekit_trace_id", default=None
)


@dataclass
class LoggingConfig:
    """Configuration for structured logging.

    Attributes:
        json_format: Emit single-line JSON records (default: True). When
            False, a plain text formatter is used instead.
        level: Root logger level as a string, e.g. ``"INFO"`` or ``"DEBUG"``.
    """

    json_format: bool = True
    level: str = "INFO"


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    The payload includes ``timestamp`` (UTC ISO-8601), ``level``, ``logger``,
    ``message``, and — when set — ``trace_id``. Keyword arguments passed via
    ``logging.Logger.info(..., extra={...})`` are merged into the payload as
    top-level fields, enabling structured fields such as ``check`` or
    ``duration_ms``. Exceptions are serialized under ``exception``.
    """

    _RESERVED_KEYS = frozenset(
        {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "taskName",
            "message",
            "asctime",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record as a single-line JSON object."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = _trace_id_var.get()
        if trace_id:
            payload["trace_id"] = trace_id
        for key, value in record.__dict__.items():
            if key in self._RESERVED_KEYS or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _install_handler(level: int, json_format: bool) -> None:
    """Attach a stream handler with the configured formatter to the root logger.

    Idempotent: repeated calls do not stack duplicate handlers.
    """
    root = logging.getLogger()
    root.setLevel(level)
    if any(getattr(handler, "_smartvintaawesomekit_json", False) for handler in root.handlers):
        return
    formatter: logging.Formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    # Marker attribute so setup_logging() stays idempotent across calls.
    handler._smartvintaawesomekit_json = True  # type: ignore[attr-defined]
    # Insert first so the JSON formatter is the one consumers find first
    # (e.g. test log captures that reuse ``root.handlers[0].formatter``).
    root.handlers.insert(0, handler)


def setup_logging(config: LoggingConfig | None = None) -> None:
    """Enable structured logging on the root logger.

    Zero-config fallback: calling ``setup_logging()`` with no arguments must
    work out of the box (JSON output at INFO level).

    Args:
        config: Optional :class:`LoggingConfig`. Defaults to JSON at INFO.
    """
    cfg = config or LoggingConfig()
    level = getattr(logging, cfg.level.upper(), logging.INFO)
    _install_handler(level, cfg.json_format)
