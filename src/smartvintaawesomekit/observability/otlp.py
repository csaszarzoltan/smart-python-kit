"""Optional OpenTelemetry/OTLP export — disabled by default, zero import-time deps.

The ``opentelemetry`` extra is optional: this module must import cleanly when
it is absent, so no opentelemetry import may happen at module load time.
"""
from __future__ import annotations


def configure_otlp_exporter(
    endpoint: str | None = None,
    service_name: str = "smartvintaawesomekit",
    enabled: bool = False,
) -> bool:
    """Enable or reconfigure the OTLP exporter.

    Returns True when the exporter is active.
    """
    raise NotImplementedError("configure_otlp_exporter is not implemented yet (RED phase)")


def otlp_enabled() -> bool:
    """Return whether OTLP export is currently enabled (default: False)."""
    raise NotImplementedError("otlp_enabled is not implemented yet (RED phase)")
