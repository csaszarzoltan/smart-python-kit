# Observability Module

Batteries-included observability for FastAPI applications — structured JSON logging,
request tracing with `trace_id` correlation, per-route metrics, and an optional
OpenTelemetry (OTLP) export hook for SigNoz, Jaeger, or Grafana.

The module is fully self-hosted by default: nothing is exported anywhere unless you
opt in, and the `opentelemetry` extra is never imported unless you enable it.

## What you get

| Concern | Component | Behavior |
|---|---|---|
| Structured logging | `setup_logging()` | Single-line JSON records on the root logger, zero-config fallback |
| Request tracing | `RequestTracingMiddleware` | Accepts or generates `X-Request-ID`, injects `trace_id` into every log record, echoes the header back |
| Metrics | `MetricsMiddleware` + `MetricsRegistry` | Per-route request count, latency samples, and error count |
| Export | `configure_otlp_exporter()` | Optional OTLP metrics export (SigNoz/Jaeger/Grafana), disabled by default |

## Installation

The core module has **zero extra dependencies** — it builds on the standard library
`logging` package and Starlette middleware.

```bash
pip install smartvintaawesomekit
```

Only install the `opentelemetry` extra when you actually want to export metrics to a
collector:

```bash
pip install "smartvintaawesomekit[opentelemetry]"
```

## Quick start

Two lines wire the module into any FastAPI app:

```python
from fastapi import FastAPI
from smartvintaawesomekit.observability import install_observability, setup_logging

setup_logging()  # structured JSON logs on the root logger

app = FastAPI(title="my-service")
app = install_observability(app)  # tracing + metrics middleware attached

@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"pong": "ok"}
```

`install_observability()` returns the same app instance, so the integration stays one
line. By default it attaches:

- `RequestTracingMiddleware` — request-id correlation,
- `MetricsMiddleware` — per-route request/error counters and latency histogram.

Both are attached with the standard `app.add_middleware(...)` API, so existing routes
and middleware are untouched.

## Request-id correlation

`RequestTracingMiddleware` correlates everything that happens during one request:

1. It reads the inbound `X-Request-ID` header — or generates a UUID when the client
   did not send one. Values that do not match a safe `[A-Za-z0-9][A-Za-z0-9-]{0,63}`
   grammar (CRLF/control characters, spaces, markup, or over-length values) are
   rejected and replaced with a fresh UUID, so inbound values are never echoed or
   logged verbatim.
2. It stores the id in a request-scoped context variable (`trace_id`).
3. Every log record emitted while the request is in flight — including records from
   third-party libraries — is serialized with that `trace_id`.
4. The middleware emits its own `request completed` record with method, path, status,
   and `duration_ms`.
5. The id is echoed back in the `X-Request-ID` response header.

A request with header `X-Request-ID: req-42` produces logs like:

```json
{"timestamp": "2026-08-05T20:33:45.359039+00:00", "level": "INFO", "logger": "app.route", "message": "ping handled", "trace_id": "req-42"}
{"timestamp": "2026-08-05T20:33:45.359588+00:00", "level": "INFO", "logger": "smartvintaawesomekit.observability.middleware", "message": "request completed", "trace_id": "req-42", "method": "GET", "path": "/ping", "status": 200, "duration_ms": 1.029}
```

Forward the same `X-Request-ID` header to downstream services and their logs carry the
same `trace_id` — that is how you follow one request across services in your log
aggregator (SigNoz, Grafana Loki, ELK, ...).

### Structured fields

`JsonFormatter` merges anything passed via `logging.Logger.info(msg, extra={...})` as
top-level fields:

```python
import logging

logging.getLogger("app.check").info(
    "readiness check completed",
    extra={"check": "database-connectivity", "ok": True, "duration_ms": 12.4},
)
```

```json
{"timestamp": "2026-08-05T20:33:45.359039+00:00", "level": "INFO", "logger": "app.check", "message": "readiness check completed", "check": "database-connectivity", "ok": true, "duration_ms": 12.4}
```

Exceptions are serialized under an `exception` field instead of a multi-line traceback.

## Metrics reference

`MetricsMiddleware` feeds an in-process, thread-safe `MetricsRegistry`. Routes are
keyed by their URL path — mapped to the route template (e.g. `/users/{user_id}`) when
the app defines one, otherwise the raw path — and request count, latency samples, and
error count are tracked per route. The registry caps distinct route keys at 1,000;
routes beyond the cap roll up under a single `_other` key, so attacker-controlled
unique paths cannot grow the registry without bound.

| Method | Description |
|---|---|
| `increment_request_count(route)` | Count one request on `route` |
| `increment_error_count(route)` | Count one error (raised exception) on `route` |
| `record_latency(route, seconds)` | Append one latency sample (seconds) for `route` |
| `request_counts()` | Snapshot of `{route: count}` |
| `error_counts()` | Snapshot of `{route: error_count}` |
| `latency_histograms()` | Snapshot of `{route: [bucket_counts]}` — per-bucket, non-cumulative latency histogram counts aligned with `histogram_buckets()` |

Read the registry from your own `/metrics` endpoint, or from application code:

```python
from smartvintaawesomekit.observability import MetricsRegistry

registry = MetricsRegistry()

@app.get("/metrics")
async def metrics() -> dict:
    return {
        "requests": registry.request_counts(),
        "errors": registry.error_counts(),
        "latency": registry.latency_histograms(),
    }
```

> **Timing note:** the middleware records the request in its `finally` block —
> after the route handler has produced its response. A `/metrics` handler
> therefore returns the snapshot as of the *previous* request; the request
> that produced the response you are reading appears on the next call. This is
> the same behavior the metrics tests assert against. When you need the count
> to include the current request, read the registry after the request completes
> (e.g. in a periodic exporter or a test assertion).

Plug the same registry into the middleware when you create it explicitly:

```python
from smartvintaawesomekit.observability import MetricsMiddleware

app.add_middleware(MetricsMiddleware, registry=registry)
```

### What is counted

- A request is counted in a `finally` block after downstream handling completes —
  including requests whose route raised — so the count is never lost to a failure.
- The latency sample covers the full downstream handling time, in seconds.
- Exceptions raised downstream are recorded as errors and re-raised, so the framework
  still produces the error response; responses with `status >= 500` are recorded as
  errors too.

## OTLP export (SigNoz / Jaeger / Grafana)

Export is **opt-in and disabled by default**. Enable it with
`configure_otlp_exporter()`:

```python
from smartvintaawesomekit.observability import configure_otlp_exporter

configure_otlp_exporter(
    endpoint="http://localhost:4318/v1/metrics",  # your collector's OTLP HTTP endpoint
    service_name="my-service",
    enabled=True,
)
```

The opentelemetry SDK is imported lazily — only when `enabled=True` is passed — so the
module imports cleanly without the `opentelemetry` extra installed. If the extra is
missing, `enabled=True` still records the opt-in intent and export no-ops until the
extra is installed (`pip install "smartvintaawesomekit[opentelemetry]"`).

Common collector endpoints:

- **SigNoz** (self-hosted or cloud): the OTLP HTTP collector, e.g.
  `http://localhost:4318/v1/metrics`. For SigNoz cloud, use the ingest URL from your
  account (OTLP HTTP endpoint; disable TLS only when your network requires it).
- **Jaeger**: Jaeger's OTLP receiver on the collector port, e.g.
  `http://localhost:4318/v1/metrics`.
- **Grafana** (Grafana Cloud / Grafana OTLP gateway):
  `https://otlp-gateway-<tenant>.grafana.net/otlp` — use the OTLP HTTP endpoint from
  your Grafana Cloud stack details.

The exporter is configured once per process; `otlp_enabled()` reports whether export
is currently active.

### Via `ObservabilityConfig`

The same opt-in is available through `install_observability()`:

```python
from fastapi import FastAPI
from smartvintaawesomekit.observability import ObservabilityConfig, install_observability, setup_logging

setup_logging()
app = FastAPI(title="my-service")
config = ObservabilityConfig(enable_otlp=True, service_name="my-service")
app = install_observability(app, config=config)
```

## Configuration reference

### `LoggingConfig`

| Field | Default | Description |
|---|---|---|
| `json_format` | `True` | Emit single-line JSON records; `False` falls back to plain text |
| `level` | `"INFO"` | Root logger level string, e.g. `"DEBUG"` |

```python
from smartvintaawesomekit.observability import LoggingConfig, setup_logging

setup_logging(LoggingConfig(json_format=True, level="DEBUG"))
```

`setup_logging()` is idempotent — repeated calls do not stack duplicate handlers.

### `ObservabilityConfig`

| Field | Default | Description |
|---|---|---|
| `enable_tracing` | `True` | Attach `RequestTracingMiddleware` |
| `enable_metrics` | `True` | Attach `MetricsMiddleware` |
| `enable_otlp` | `False` | Opt into OTLP export (requires the `opentelemetry` extra to actually export) |
| `service_name` | `"smartvintaawesomekit"` | Service name used for OTLP resource attributes |
| `log_level` | `"INFO"` | Log level used by `setup_logging()` |

## Readiness checks

The existing readiness checks (`smartvintaawesomekit.readiness.check_database`,
`check_application_import`) now emit structured log records such as:

```json
{"timestamp": "2026-08-05T20:33:45.359039+00:00", "level": "INFO", "logger": "smartvintaawesomekit.readiness", "message": "readiness check completed", "check": "database-connectivity", "ok": true, "code": "database_ready", "duration_ms": 0.62}
```

With `MetricsMiddleware` attached, `/health` traffic is also counted per route, so
health and readiness traffic shows up in your dashboards automatically.

## Generated projects

Every project scaffolded with `smartvintaawesomekit init` (all presets) now includes
observability by default in `app/main.py`:

```python
from fastapi import FastAPI
from app.config import settings
from smartvintaawesomekit.observability import install_observability, setup_logging

setup_logging()

app = FastAPI(title=settings.app_name, version="0.1.0", description="Generated with SmartVintaAwesomeKit")
app = install_observability(app)
```

No further wiring is required — generated projects get structured logs and
request-id correlation out of the box.
