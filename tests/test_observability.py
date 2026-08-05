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
from fastapi import FastAPI, HTTPException
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
            "histogram_buckets",
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

        buckets = registry.histogram_buckets()
        counts = registry.latency_histograms()["/slow"]
        assert len(counts) == len(buckets)
        assert sum(counts) >= 1  # the sample landed in a bucket
        assert all(count >= 0 for count in counts)

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


# ---------------------------------------------------------------------------
# Section 3 — regression tests for tech-lead review findings
# (B1: request-id validation; B2: bounded metrics storage;
#  M1: 5xx error counting; M2: logging formatter-kind switching; M3: OTLP guard)
# ---------------------------------------------------------------------------


class TestRequestIdValidation:
    """B1: inbound X-Request-ID is validated; non-conforming values are regenerated."""

    @staticmethod
    def _client() -> TestClient:
        app = FastAPI()

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"pong": "ok"}

        app.add_middleware(RequestTracingMiddleware)
        return TestClient(app)

    def test_request_tracing_regenerates_non_conforming_request_id(self) -> None:
        client = self._client()
        inbound = "bad value with spaces!!"
        response = client.get("/ping", headers={"X-Request-ID": inbound})
        assert response.status_code == 200
        echoed = response.headers.get("X-Request-ID")
        assert echoed is not None
        assert echoed != inbound  # regenerated, not reflected

    def test_request_tracing_regenerates_overlength_request_id(self) -> None:
        client = self._client()
        inbound = "x" * 100  # exceeds the 64-char limit
        response = client.get("/ping", headers={"X-Request-ID": inbound})
        echoed = response.headers.get("X-Request-ID")
        assert echoed is not None
        assert echoed != inbound
        assert len(echoed) <= 64

    def test_request_tracing_regenerates_crlf_request_id(self) -> None:
        client = self._client()
        inbound = "abc\r\nX-Evil: injected"
        response = client.get("/ping", headers={"X-Request-ID": inbound})
        echoed = response.headers.get("X-Request-ID")
        assert echoed is not None
        assert echoed != inbound
        assert "\r" not in echoed and "\n" not in echoed
        assert "X-Evil" not in echoed  # no raw echo of the CRLF payload

    def test_request_tracing_accepts_max_length_conforming_request_id(self) -> None:
        client = self._client()
        inbound = "a" + ("-b" * 31)  # 1 + 62 = 63 chars, within the grammar
        response = client.get("/ping", headers={"X-Request-ID": inbound})
        assert response.headers.get("X-Request-ID") == inbound


class TestMetricsRegistryBounded:
    """B2: bounded storage — fixed histogram buckets + capped route keys."""

    def test_many_samples_keep_bounded_storage(self) -> None:
        registry = MetricsRegistry()
        for _ in range(10_000):
            registry.record_latency("/r", 0.05)
        counts = registry.latency_histograms()["/r"]
        assert len(counts) == len(registry.histogram_buckets())  # fixed size
        assert sum(counts) == 10_000  # every sample counted

    def test_samples_land_in_correct_histogram_bucket(self) -> None:
        """Samples land in exactly one bucket (per-bucket, non-cumulative).

        Documented contract: ``counts[i]`` is the number of samples in bucket
        ``i``, i.e. latency in ``(buckets[i-1], buckets[i]]`` seconds, with
        the first bucket holding ``s <= buckets[0]``.
        """
        buckets = MetricsRegistry().histogram_buckets()
        registry = MetricsRegistry()
        registry.record_latency("/r", 0.0)        # below first bound -> bucket 0
        registry.record_latency("/r", 0.05)       # exactly on the 0.05s bound -> its own bucket
        registry.record_latency("/r", 0.050001)   # just above 0.05s -> (0.05, 0.1] bucket
        registry.record_latency("/r", 999.0)      # past last finite bound -> inf catch-all
        counts = registry.latency_histograms()["/r"]
        assert counts[0] == 1                        # s <= buckets[0]
        assert counts[buckets.index(0.05)] == 1      # right-inclusive bound placement
        assert counts[buckets.index(0.05) + 1] == 1  # sample between 0.05 and 0.1
        assert counts[-1] == 1                       # inf bucket holds the 999s sample
        assert sum(counts) == 4                      # every sample counted exactly once
        # Per-bucket, not cumulative: a cumulative histogram would be monotonic
        # non-decreasing (counts[1] >= counts[0]).
        assert counts[0] == 1 and counts[1] == 0

    def test_unique_route_flood_is_capped(self) -> None:
        registry = MetricsRegistry()
        for i in range(10_000):
            registry.increment_request_count(f"/unique-{i}")
        counts = registry.request_counts()
        assert len(counts) <= MetricsRegistry.MAX_ROUTES + 1
        assert counts.get(MetricsRegistry.OTHER_ROUTE, 0) == 10_000 - MetricsRegistry.MAX_ROUTES

    def test_middleware_maps_paths_to_route_templates(self) -> None:
        app = FastAPI()

        @app.get("/users/{user_id}")
        async def get_user(user_id: str) -> dict[str, str]:
            return {"id": user_id}

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app)

        client.get("/users/1")
        client.get("/users/2")

        counts = registry.request_counts()
        assert counts["/users/{user_id}"] == 2  # both requests share one template key
        assert "/users/1" not in counts and "/users/2" not in counts

    def test_middleware_unique_path_flood_is_bounded(self) -> None:
        app = FastAPI()

        @app.get("/known")
        async def known() -> dict[str, str]:
            return {"ok": "yes"}

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app)

        for i in range(MetricsRegistry.MAX_ROUTES + 250):
            client.get(f"/unknown-{i}")

        counts = registry.request_counts()
        assert len(counts) <= MetricsRegistry.MAX_ROUTES + 1


class TestMetricsMiddleware5xx:
    """M1: responses with status >= 500 are counted as errors."""

    def test_metrics_middleware_counts_http_500_as_error(self) -> None:
        app = FastAPI()

        @app.get("/fail500")
        async def fail500() -> dict[str, str]:
            raise HTTPException(status_code=500, detail="boom")

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app)

        response = client.get("/fail500")
        assert response.status_code == 500
        assert registry.error_counts()["/fail500"] == 1

    def test_metrics_middleware_does_not_count_http_404_as_error(self) -> None:
        app = FastAPI()

        @app.get("/known")
        async def known() -> dict[str, str]:
            return {"ok": "yes"}

        registry = MetricsRegistry()
        app.add_middleware(MetricsMiddleware, registry=registry)
        client = TestClient(app)

        client.get("/missing")
        assert registry.error_counts() == {}


class TestLoggingFormatterKindSwitching:
    """M2: setup_logging() swaps formatters when the json/text kind changes."""

    @staticmethod
    def _managed_handlers() -> list[logging.Handler]:
        return [
            handler
            for handler in logging.getLogger().handlers
            if getattr(handler, "_smartvintaawesomekit_json", None) is not None
        ]

    def test_setup_logging_switches_json_to_text_to_json(self) -> None:
        from smartvintaawesomekit.observability.logging import JsonFormatter

        setup_logging(LoggingConfig(json_format=True))
        managed = self._managed_handlers()
        assert len(managed) == 1
        assert isinstance(managed[0].formatter, JsonFormatter)

        setup_logging(LoggingConfig(json_format=False))
        managed = self._managed_handlers()
        assert len(managed) == 1  # no duplicate handler stacked
        assert not isinstance(managed[0].formatter, JsonFormatter)

        setup_logging(LoggingConfig(json_format=True))
        managed = self._managed_handlers()
        assert len(managed) == 1
        assert isinstance(managed[0].formatter, JsonFormatter)

    def test_setup_logging_same_kind_is_idempotent(self) -> None:
        setup_logging(LoggingConfig(json_format=True))
        managed = self._managed_handlers()
        assert len(managed) == 1
        setup_logging(LoggingConfig(json_format=True))
        assert self._managed_handlers() == managed  # same handler, no stacking


class TestOtlpConstructionGuard:
    """M3: exporter construction failures are swallowed, never raised."""

    def test_otlp_configure_swallows_construction_failure(self, monkeypatch: Any) -> None:
        from smartvintaawesomekit.observability import otlp

        class BoomExporter:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ValueError("bad endpoint")

        class FakeMetrics:
            class Export:
                PeriodicExportingMetricReader = object

            MeterProvider = object
            set_meter_provider = staticmethod(lambda *args: None)

        class FakeResources:
            Resource = type("Resource", (), {"create": staticmethod(lambda *args: None)})

        def fake_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "opentelemetry.sdk.metrics":
                return FakeMetrics
            if name == "opentelemetry.sdk.resources":
                return FakeResources
            if name == "opentelemetry.exporter.otlp.proto.http.metric_exporter":
                return type("FakeExporterMod", (), {"OTLPMetricExporter": BoomExporter})
            raise ImportError(name)

        monkeypatch.setattr(otlp.importlib, "import_module", fake_import_module)
        # Must not raise, and must still record the opt-in intent.
        assert otlp.configure_otlp_exporter(endpoint="http://invalid:1", enabled=True) is True
        assert otlp.otlp_enabled() is True
        otlp.configure_otlp_exporter(enabled=False)  # reset for later tests
