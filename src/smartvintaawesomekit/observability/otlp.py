"""Optional OpenTelemetry/OTLP export — disabled by default, zero import-time deps.

The ``opentelemetry`` extra is optional: this module must import cleanly when
it is absent, so no opentelemetry import may happen at module load time. The
SDK is imported lazily — only inside :func:`configure_otlp_exporter` when
``enabled=True`` — and any failure is swallowed, because the module must keep
working without the extra.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass
class _OtlpState:
    """Module-level OTLP configuration state."""

    enabled: bool = False
    endpoint: str | None = None
    service_name: str = "smartvintaawesomekit"


_STATE = _OtlpState()


def _install_exporter(endpoint: str | None, service_name: str) -> None:
    """Best-effort wiring of an OTLP metrics exporter (no-op without the extra).

    Imports the opentelemetry SDK lazily and configures a
    :class:`PeriodicExportingMetricReader` backed by an OTLP HTTP exporter.
    Any failure — most commonly the ``opentelemetry`` extra not being
    installed — leaves the process untouched; the enabled flag still records
    the opt-in intent.
    """
    try:
        sdk_metrics = importlib.import_module("opentelemetry.sdk.metrics")
        resources = importlib.import_module("opentelemetry.sdk.resources")
        exporter_mod = importlib.import_module(
            "opentelemetry.exporter.otlp.proto.http.metric_exporter"
        )
    except (ImportError, ModuleNotFoundError):
        return
    reader_class = sdk_metrics.export.PeriodicExportingMetricReader
    exporter_class = exporter_mod.OTLPMetricExporter
    exporter = exporter_class(endpoint=endpoint) if endpoint else exporter_class()
    reader = reader_class(exporter)
    resource = resources.Resource.create({"service.name": service_name})
    provider = sdk_metrics.MeterProvider(resource=resource, metric_readers=[reader])
    sdk_metrics.set_meter_provider(provider)


def configure_otlp_exporter(
    endpoint: str | None = None,
    service_name: str = "smartvintaawesomekit",
    enabled: bool = False,
) -> bool:
    """Enable or reconfigure the OTLP exporter.

    The opentelemetry SDK is imported lazily — only when ``enabled`` is True —
    so the module imports cleanly without the optional extra. When the extra
    is absent, ``enabled=True`` still records the opt-in intent and export
    becomes a no-op until the extra is installed.

    Args:
        endpoint: OTLP collector endpoint URL (default: SDK default).
        service_name: Resource service name (default: ``smartvintaawesomekit``).
        enabled: Opt in (True) or out (False) of OTLP export.

    Returns:
        True when the exporter is active.
    """
    _STATE.endpoint = endpoint
    _STATE.service_name = service_name
    if not enabled:
        _STATE.enabled = False
        return False
    _install_exporter(endpoint=endpoint, service_name=service_name)
    _STATE.enabled = True
    return True


def otlp_enabled() -> bool:
    """Return whether OTLP export is currently enabled (default: False)."""
    return _STATE.enabled
