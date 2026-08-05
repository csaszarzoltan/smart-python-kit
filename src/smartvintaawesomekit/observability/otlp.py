"""Optional OpenTelemetry/OTLP export — disabled by default, zero import-time deps.

The ``opentelemetry`` extra is optional: this module must import cleanly when
it is absent, so no opentelemetry import may happen at module load time. The
SDK is imported lazily — only inside :func:`configure_otlp_exporter` when
``enabled=True`` — and any failure (missing extra, invalid endpoint URL, SDK
errors) is logged and swallowed, because the module must keep working without
the extra and must not crash application startup.
"""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass

logger = logging.getLogger("smartvintaawesomekit.observability.otlp")


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
    Any failure — the ``opentelemetry`` extra not being installed, an invalid
    endpoint URL, or an SDK error — is logged and swallowed, so the caller
    (e.g. ``install_observability`` at startup) never crashes; the enabled
    flag still records the opt-in intent.
    """
    try:
        sdk_metrics = importlib.import_module("opentelemetry.sdk.metrics")
        resources = importlib.import_module("opentelemetry.sdk.resources")
        exporter_mod = importlib.import_module(
            "opentelemetry.exporter.otlp.proto.http.metric_exporter"
        )
    except (ImportError, ModuleNotFoundError):
        return
    try:
        reader_class = sdk_metrics.export.PeriodicExportingMetricReader
        exporter_class = exporter_mod.OTLPMetricExporter
        exporter = exporter_class(endpoint=endpoint) if endpoint else exporter_class()
        reader = reader_class(exporter)
        resource = resources.Resource.create({"service.name": service_name})
        provider = sdk_metrics.MeterProvider(resource=resource, metric_readers=[reader])
        sdk_metrics.set_meter_provider(provider)
    except Exception:
        logger.exception("failed to configure OTLP exporter; export stays disabled")


def configure_otlp_exporter(
    endpoint: str | None = None,
    service_name: str = "smartvintaawesomekit",
    enabled: bool = False,
) -> bool:
    """Enable or reconfigure the OTLP exporter.

    The opentelemetry SDK is imported lazily — only when ``enabled`` is True —
    so the module imports cleanly without the optional extra.

    Args:
        endpoint: OTLP collector endpoint URL (default: SDK default).
        service_name: Resource service name (default: ``smartvintaawesomekit``).
        enabled: Opt in (True) or out (False) of OTLP export.

    Returns:
        True when OTLP export is opted in. The exporter only becomes active
        once the ``opentelemetry`` extra is installed and construction
        succeeds; until then the return value records opt-in intent and
        export no-ops (construction failures are logged, never raised).
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
    """Return whether OTLP export is opted in (default: False)."""
    return _STATE.enabled
