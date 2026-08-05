"""Pre-development TDD suite for the observability module.

Layout:
- Section 1 (interface): public API surface, signatures, config defaults.
  These tests PASS immediately against the NotImplementedError stubs.
- Section 2 (behavioral): runtime behavior. These tests FAIL with
  NotImplementedError during the RED phase and pass once the developer
  implements ``src/smartvintaawesomekit/observability/``.

The integration test in Section 2 hits a REAL FastAPI TestClient path (no
mocks): request -> RequestTracingMiddleware -> emitted log record, asserting
the record's ``trace_id`` equals the inbound ``X-Request-ID`` header.
"""
from __future__ import annotations

import inspect
import io
import json
import logging
import sys
from dataclasses import is_dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smartvintaawesomekit.observability import (
    LoggingConfig,
    MetricsMiddleware,
    MetricsRegistry,
    ObservabilityConfig,
    RequestTracingMiddleware,
    configure_otlp_exporter,
    install_observability,
    otlp_enabled,
    setup_logging,
)
from smartvintaawesomekit.readiness import check_database


class LogCapture:
    """Attach a stream handler to the root logger and read emitted lines."""

    def __init__(self) -> None:
        self.stream = io.StringIO()
        self._handler = logging.StreamHandler(self.stream)

    def attach(self) -> None:
        """Attach after setup_logging() so the impl's own formatter is reused."""
        root = logging.getLogger()
        formatter = next(
            (handler.formatter for handler in root.handlers if handler.formatter is not None),
            logging.Formatter("%(message)s"),
        )
        self._handler.setFormatter(formatter)
        root.addHandler(self._handler)

    def lines(self) -> list[str]:
        for handler in list(logging.getLogger().handlers):
            handler.flush()
        return [line for line in self.stream.getvalue().splitlines() if line.strip()]

    def detach(self) -> None:
        logging.getLogger().removeHandler(self._handler)


@pytest.fixture
def log_capture() -> LogCapture:
    capture = LogCapture()
    yield capture
    capture.detach()


def _parsed_lines(capture: LogCapture) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in capture.lines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
    return records


# ---------------------------------------------------------------------------
# Section 1 — interface tests (PASS during RED)
# ---------------------------------------------------------------------------


class TestPublicApiSurface:
    """Interface: module layout and exported names."""

    def test_observability_package_importable(self) -> None:
        from smartvintaawesomekit import observability

        assert observability.__name__ == "smartvintaawesomekit.observability"

    def test_public_api_functions_are_callable(self) -> None:
        assert callable(setup_logging)
        assert callable(install_observability)
        assert callable(configure_otlp_exporter)
        assert callable(otlp_enabled)

    def test_middleware_and_registry_classes_exist(self) -> None:
        assert inspect.isclass(RequestTracingMiddleware)
        assert inspect.isclass(MetricsMiddleware)
        assert inspect.isclass(MetricsRegistry)

    def test_config_classes_are_dataclasses(self) -> None:
        assert is_dataclass(LoggingConfig)
        assert is_dataclass(ObservabilityConfig)


class TestSignatures:
    """Interface: pinned public API signatures."""

    def test_setup_logging_signature(self) -> None:
        sig = inspect.signature(setup_logging)
        assert "config" in sig.parameters
        assert sig.parameters["config"].default is None

    def test_install_observability_signature(self) -> None:
        sig = inspect.signature(install_observability)
        assert "app" in sig.parameters
        assert "config" in sig.parameters
        assert sig.parameters["config"].default is None

    def test_request_tracing_middleware_init_signature(self) -> None:
        sig = inspect.signature(RequestTracingMiddleware.__init__)
        params = sig.parameters
        assert "app" in params
        assert "header" in params
        assert params["header"].default == "X-Request-ID"

    def test_request_tracing_middleware_dispatch_signature(self) -> None:
        sig = inspect.signature(RequestTracingMiddleware.dispatch)
        assert "request" in sig.parameters
        assert "call_next" in sig.parameters

    def test_metrics_middleware_init_signature(self) -> None:
        sig = inspect.signature(MetricsMiddleware.__init__)
        params = sig.parameters
        assert "app" in params
        assert "registry" in params
        assert params["registry"].default is None

    def test_metrics_registry_methods_exist(self) -> None:
        for name in (
            "increment_request_count",
            "increment_error_count",
            "record_latency",
            "request_counts",
            "error_counts",
            "latency_histograms",
        ):
            assert callable(getattr(MetricsRegistry, name)), name

    def test_configure_otlp_exporter_signature(self) -> None:
        sig = inspect.signature(configure_otlp_exporter)
        params = sig.parameters
        assert "endpoint" in params
        assert params["endpoint"].default is None
        assert "service_name" in params
        assert params["service_name"].default == "smartvintaawesomekit"
        assert "enabled" in params
        assert params["enabled"].default is False


class TestConfigDefaults:
    """Interface: zero-config defaults."""

    def test_logging_config_defaults(self) -> None:
        config = LoggingConfig()
        assert config.json_format is True
        assert config.level == "INFO"

    def test_observability_config_defaults(self) -> None:
        config = ObservabilityConfig()
        assert config.enable_tracing is True
        assert config.enable_metrics is True
        assert config.enable_otlp is False  # OTLP disabled by default
        assert config.service_name == "smartvintaawesomekit"
        assert config.log_level == "INFO"


class TestOtlpImport:
    """Interface: the optional opentelemetry extra must not be required."""

    def test_otlp_module_imports_without_opentelemetry(self) -> None:
        from smartvintaawesomekit.observability import otlp

        assert "opentelemetry" not in sys.modules
        assert callable(otlp.configure_otlp_exporter)
        assert callable(otlp.otlp_enabled)


# ---------------------------------------------------------------------------
# Section 2 — behavioral tests (FAIL with NotImplementedError during RED)
# ---------------------------------------------------------------------------


class TestStructuredLogging:
    """Behavioral: setup_logging() enables structured JSON output."""

    def test_setup_logging_zero_config_installs_json_formatter(self) -> None:
        setup_logging()  # zero-config fallback — no arguments required
        root = logging.getLogger()
        formatters = [handler.formatter for handler in root.handlers if handler.formatter is not None]
        assert formatters, "setup_logging() must install a handler with a formatter"
        record = logging.LogRecord(
            "observability.test", logging.INFO, __file__, 1, "structured message", None, None
        )
        payload = json.loads(formatters[0].format(record))  # must be valid JSON
        assert isinstance(payload, dict)

    def test_setup_logging_accepts_explicit_config(self) -> None:
        setup_logging(LoggingConfig(json_format=True, level="DEBUG"))
        root = logging.getLogger()
        formatters = [handler.formatter for handler in root.handlers if handler.formatter is not None]
        assert formatters
        record = logging.LogRecord(
            "observability.test", logging.DEBUG, __file__, 1, "debug message", None, None
        )
        payload = json.loads(formatters[0].format(record))
        assert isinstance(payload, dict)


class TestRequestTracingMiddleware:
    """Behavioral: accept/generate X-Request-ID and echo it in the response."""

    def test_request_tracing_echoes_incoming_request_id(self) -> None:
        app = FastAPI()

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"pong": "ok"}

        app.add_middleware(RequestTracingMiddleware)
        client = TestClient(app)
        request_id = "incoming-req-42"
        response = client.get("/ping", headers={"X-Request-ID": request_id})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == request_id

    def test_request_tracing_generates_request_id_when_absent(self) -> None:
        app = FastAPI()

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"pong": "ok"}

        app.add_middleware(RequestTracingMiddleware)
        client = TestClient(app)
        response = client.get("/ping")
        assert response.status_code == 200
        generated = response.headers.get("X-Request-ID")
        assert generated is not None and len(generated) > 0


class TestInstallObservabilityIntegration:
    """Behavioral: one-line integration via install_observability.

    Real-path integration test required by the acceptance criteria: a
    TestClient request hits a real route, the tracing middleware echoes the
    inbound X-Request-ID, and the emitted log record carries the same value
    as ``trace_id`` — no mocks anywhere.
    """

    def test_install_observability_correlates_request_id_with_log_record(
        self, log_capture: LogCapture
    ) -> None:
        app = FastAPI()

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            logging.getLogger("observability.route").info("ping handled")
            return {"pong": "ok"}

        setup_logging()
        log_capture.attach()

        installed = install_observability(app)
        assert installed is app  # one-line integration contract

        request_id = "corr-0001"
        client = TestClient(installed)
        response = client.get("/ping", headers={"X-Request-ID": request_id})

        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == request_id

        records = _parsed_lines(log_capture)
        assert any(record.get("trace_id") == request_id for record in records), (
            f"no log record carried trace_id={request_id!r}; got {log_capture.lines()!r}"
        )


class TestMetricsMiddleware:
    """Behavioral: per-route counters, latency histogram, error counters."""

    def test_metrics_middleware_counts_requests_per_route(self) -> None:
        app = FastAPI()

        @app.get("/metrics-route")
        async def route() -> dict[str, str]:
            return {"ok": "yes"}

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app)

        client.get("/metrics-route")
        client.get("/metrics-route")
        client.get("/other")

        counts = registry.request_counts()
        assert counts["/metrics-route"] == 2
        assert counts["/other"] == 1

    def test_metrics_middleware_records_latency_histogram(self) -> None:
        app = FastAPI()

        @app.get("/slow")
        async def slow() -> dict[str, str]:
            return {"ok": "yes"}

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app)

        client.get("/slow")

        samples = registry.latency_histograms()["/slow"]
        assert len(samples) >= 1
        assert all(sample >= 0 for sample in samples)

    def test_metrics_middleware_increments_error_counter_per_route(self) -> None:
        app = FastAPI()

        @app.get("/boom")
        async def boom() -> dict[str, str]:
            raise RuntimeError("boom")

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/boom")
        assert response.status_code == 500
        assert registry.error_counts()["/boom"] == 1


class TestReadinessObservability:
    """Behavioral: readiness/health endpoints emit structured logs and metrics."""

    def test_health_endpoint_emits_structured_log_and_metrics_counter(
        self, log_capture: LogCapture
    ) -> None:
        app = FastAPI()

        @app.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "healthy"}

        registry = MetricsRegistry()
        app.add_middleware(RequestTracingMiddleware)
        app.add_middleware(MetricsMiddleware, registry=registry)

        setup_logging()
        log_capture.attach()

        request_id = "health-rid-9"
        client = TestClient(app)
        response = client.get("/health", headers={"X-Request-ID": request_id})

        assert response.status_code == 200
        assert registry.request_counts()["/health"] == 1
        records = _parsed_lines(log_capture)
        assert any(record.get("trace_id") == request_id for record in records), (
            f"health request log missing trace_id={request_id!r}; got {log_capture.lines()!r}"
        )

    def test_readiness_check_emits_structured_log(self, log_capture: LogCapture, tmp_path: Any) -> None:
        setup_logging()
        log_capture.attach()

        project = tmp_path / "proj"
        project.mkdir()
        (project / ".env").write_text("DATABASE_URL=sqlite+aiosqlite:///./ready.db\n", encoding="utf-8")

        result = check_database(project)
        assert result["ok"] is True

        records = _parsed_lines(log_capture)
        assert any("database-connectivity" in json.dumps(record) for record in records), (
            f"readiness check did not emit a structured log; got {log_capture.lines()!r}"
        )


class TestOtlpExport:
    """Behavioral: OTLP exporter is disabled by default and opt-in via config."""

    def test_otlp_exporter_disabled_by_default(self) -> None:
        assert otlp_enabled() is False

    def test_otlp_exporter_opt_in_enables_export(self) -> None:
        assert configure_otlp_exporter(endpoint="http://localhost:4317", enabled=True) is True
        assert otlp_enabled() is True
        configure_otlp_exporter(enabled=False)  # reset for later tests
