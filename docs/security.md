# Security hardening guide

The `smartvintaawesomekit.security` module hardens a FastAPI application with five
ASGI middleware components, wired in a single call:

| # | Component | Middleware class | What it does |
|---|-----------|------------------|--------------|
| 1 | CORS hardening | `CORSHardeningMiddleware` | Validates `Origin` against an allow-list; rejects `*` in production |
| 2 | Rate limiting | `RateLimitMiddleware` | Token-bucket limits per client, with optional per-route limits |
| 3 | Request size limit | `RequestSizeMiddleware` | Rejects oversized bodies with `413` |
| 4 | Input sanitization | `InputSanitizationMiddleware` | Strips null bytes; blocks SQL injection / XSS patterns |
| 5 | Security headers | `SecurityHeadersMiddleware` | Adds HSTS, CSP, X-Frame-Options, and friends to every response |

All components are on by default; each can be disabled independently via
[`SecurityMiddlewareConfig`](#configuration-reference).

## Quick start

```python
from fastapi import FastAPI
from smartvintaawesomekit.security import add_security_middleware

app = FastAPI(title="my-service")
app = add_security_middleware(app)  # returns the same app instance
```

That single call attaches all five middleware in the order listed above. A complete,
runnable example lives in [`examples/security_example.py`](../examples/security_example.py).

### Production mode

CORS hardening needs to know whether the app runs in production (where wildcard
origins are rejected). `add_security_middleware` resolves this automatically:

```python
from smartvintaawesomekit.config import SmartConfig

app = add_security_middleware(app)                # is_production from SmartConfig()
app = add_security_middleware(app, is_production=True)   # or pin it explicitly
```

When `is_production=True` (or `SmartConfig().environment == "production"`) and the
config still allows the wildcard origin `*`, `CORSHardeningMiddleware` raises a
`ValueError` at startup with a clear message — misconfiguration fails fast instead
of shipping.

## Configuration reference

`SecurityMiddlewareConfig` (aliased as `SecurityConfig` for backward compatibility)
is a plain dataclass with validated defaults.

### Feature toggles

| Field | Default | Description |
|-------|---------|-------------|
| `enable_rate_limiting` | `True` | Attach `RateLimitMiddleware` |
| `enable_security_headers` | `True` | Attach `SecurityHeadersMiddleware` |
| `enable_cors_hardening` | `True` | Attach `CORSHardeningMiddleware` |
| `enable_request_size_limit` | `True` | Attach `RequestSizeMiddleware` |
| `enable_input_sanitization` | `True` | Attach `InputSanitizationMiddleware` |

### Rate limiting

| Field | Default | Description |
|-------|---------|-------------|
| `rate_limit_requests` | `100` | Max requests per client per window |
| `rate_limit_window_seconds` | `60` | Window length in seconds |
| `rate_limit_per_route` | `{}` | `{route: (requests, window_seconds)}` overrides |

### Security headers

| Field | Default | Description |
|-------|---------|-------------|
| `hsts_max_age` | `31536000` | `Strict-Transport-Security` max-age (1 year) |
| `hsts_include_subdomains` | `True` | Appends `includeSubDomains` |
| `hsts_preload` | `False` | Appends `preload` |
| `csp_policy` | `"default-src 'self'"` | `Content-Security-Policy` value |
| `frame_options` | `"DENY"` | `X-Frame-Options` value |
| `content_type_options` | `"nosniff"` | `X-Content-Type-Options` value |
| `xss_protection` | `"1; mode=block"` | `X-XSS-Protection` value |
| `referrer_policy` | `"strict-origin-when-cross-origin"` | `Referrer-Policy` value |

### CORS hardening

| Field | Default | Description |
|-------|---------|-------------|
| `allowed_origins` | `["*"]` | Allow-list of origins |
| `allowed_methods` | `["*"]` | Allow-list of HTTP methods |
| `allowed_headers` | `["*"]` | Allow-list of request headers |
| `allow_credentials` | `True` | Emits `Access-Control-Allow-Credentials: true` |
| `reject_wildcard_in_production` | `True` | Reject `*` origin when `is_production` |

### Request size limit

| Field | Default | Description |
|-------|---------|-------------|
| `max_body_size` | `1048576` | Max body bytes (1 MiB) |
| `max_body_size_exceeded_message` | `"Request body exceeds maximum allowed size"` | Message in the `413` response |

### Input sanitization

| Field | Default | Description |
|-------|---------|-------------|
| `strip_null_bytes` | `True` | Remove `\x00` from query params and body |
| `detect_sql_injection` | `True` | Match SQLi patterns (see below) |
| `detect_xss` | `True` | Match XSS patterns (see below) |
| `sql_injection_patterns` | `[]` | Extra regex patterns appended to the defaults |
| `xss_patterns` | `[]` | Extra regex patterns appended to the defaults |

## Rate limiting: token bucket

`RateLimitMiddleware` keeps one token bucket per client per route. The bucket holds
`requests` tokens and refills continuously at `requests / window_seconds` tokens per
second (wall-clock time via `time.monotonic()`). Each request consumes one token;
when the bucket is empty the request is rejected.

The client is identified as, in priority order:

1. `request.state.user["sub"]` — the authenticated user (set by `AuthMiddleware`),
   so limits follow the account, not the IP,
2. the `X-Forwarded-For` first hop, when present,
3. `request.client.host`.

Rejected requests get:

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 3
}
```

with status `429` and a `Retry-After` header (seconds, rounded up). Idle buckets are
garbage-collected on a 60-second sweep, so memory does not grow with abandoned
clients.

### Per-route limits

Pass `rate_limit_per_route` to give specific paths their own (requests, window)
pair. The route key matches the request path exactly, or by prefix when the pattern
ends in `*`; anything else falls back to the global limit.

```python
from smartvintaawesomekit.security import SecurityMiddlewareConfig, add_security_middleware

config = SecurityMiddlewareConfig(
    rate_limit_requests=100,          # global default
    rate_limit_window_seconds=60,
    rate_limit_per_route={
        "/login": (5, 60),            # 5 attempts/minute — brute-force protection
        "/api/v1/": (1000, 60),       # prefix match: whole API namespace
    },
)
app = add_security_middleware(app, config)
```

Per-route limits above the global limit produce a warning from
[`validate_security_config`](#validation) — they are valid, but probably not what
you meant.

## Security headers

`SecurityHeadersMiddleware` adds these headers to every response:

| Header | Default value |
|--------|---------------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'` |

HSTS is composed from `hsts_max_age`, `hsts_include_subdomains`, and `hsts_preload`:

```text
max-age=31536000; includeSubDomains            # defaults
max-age=31536000; includeSubDomains; preload   # with hsts_preload=True
```

## CORS hardening: production vs development

| | Development (`is_production=False`) | Production (`is_production=True`) |
|---|------------------------------------|----------------------------------|
| Wildcard origin `*` | Allowed; echoed as `Access-Control-Allow-Origin: *` | **Rejected at startup** (`ValueError`) when `reject_wildcard_in_production=True`; disallowed origins get `403` |
| Allowed origin | Echoed back as `Access-Control-Allow-Origin: <origin>` | Same |
| Credentials | `Access-Control-Allow-Credentials: true` | Same |
| Preflight | `200` + `Access-Control-Max-Age: 86400` + `Vary: Origin` | Same |
| Disallowed origin | No CORS headers on actual requests | `403` on preflight |

Preflight (`OPTIONS`) requests always include `Vary: Origin` so caches key on the
origin header correctly.

> **Note:** `*` with `allow_credentials=True` is a contradiction browsers reject —
> `validate_security_config` flags it as critical. In production, always set
> explicit origins.

## Request size limits

`RequestSizeMiddleware` reads `Content-Length` and returns `413` when it exceeds
`max_body_size`:

```json
{
  "detail": "Request body exceeds maximum allowed size",
  "max_size_bytes": 1048576
}
```

**Known limitation:** chunked transfer-encoding requests (no `Content-Length`) are
not stream-counted by this middleware. For comprehensive protection in production,
combine it with a reverse proxy (`nginx`, `traefik`) or the ASGI server limit
(`uvicorn --limit-max-request-body-size`).

## Input sanitization

The middleware sanitizes **query parameters and request bodies** (JSON and form).

- `strip_null_bytes` removes `\x00` from every value.
- Bodies larger than 1 MiB are skipped (the request-size middleware handles those).
- On a threat match the request is rejected with `400`:

```json
{
  "detail": "Threat detected in query param 'q': SQL injection pattern detected: <regex>"
}
```

For bodies: `{"detail": "Threat detected in request body: <pattern>"}`.

### Detected patterns

Default SQL injection patterns (all case-insensitive, compiled with a `re.TIMEOUT`
guard against ReDoS):

```text
union\s+select            or\s+1\s*=\s*1            or\s+'1'\s*=\s*'1'
drop\s+table              insert\s+into            delete\s+from
update\s+\w+\s+set        exec\s*\(                execute\s*\(
xp_cmdshell               sp_executesql            --\s*$
;\s*$                     '\s*;\s*--
```

Default XSS patterns:

```text
<script[^>]*>   </script>   javascript:   onerror\s*=   onload\s*=
onclick\s*=     onmouseover\s*=   eval\s*\(   expression\s*\(   vbscript:
data:text/html
```

### Customizing the pattern lists

`sql_injection_patterns` and `xss_patterns` are **appended** to the defaults — you
cannot remove a built-in pattern, only add your own:

```python
from smartvintaawesomekit.security import SecurityMiddlewareConfig, add_security_middleware

config = SecurityMiddlewareConfig(
    sql_injection_patterns=[r"pg_sleep\s*\("],
    xss_patterns=[r"<iframe[^>]*>"],
)
app = add_security_middleware(app, config)
```

Sanitization is a defense-in-depth layer, not a replacement for parameterized
queries and proper output encoding.

## `smartvintaawesomekit security audit`

Audit your current security posture from the CLI. It checks middleware config,
expected headers, CORS settings, and rate limiting:

```bash
smartvintaawesomekit security audit --project . --environment production
```

Human output:

```text
Security Audit — WARNINGS
Environment: production
Checks: 16 (warnings=2, critical=0)

  ✓ Rate limiting: enabled
  ✓ Security headers: enabled
  ...
  ⚠ CORS wildcard origin: warning: wildcard '*' in use
  ✗ Header: X-Content-Type-Options: missing (security headers disabled)
```

JSON output (`--json`) mirrors the structured report:

```json
{
  "exit_code": 1,
  "status": "warnings",
  "environment": "production",
  "checks": [
    {"check": "Rate limiting", "status": "enabled", "severity": "info"}
  ],
  "total_checks": 16,
  "warnings": 2,
  "critical": 0
}
```

**Exit codes:** `0` = pass, `1` = warnings, `2` = critical. Use `--check` to make CI
fail on a non-zero audit:

```bash
smartvintaawesomekit security audit --project . --environment production --check --json
```

The command reads `app/config.py` from the target project (if present) and pulls
security settings from `settings.security` and CORS settings from `settings.cors`,
so the audit reflects what the app actually runs with.

### Validation

`validate_security_config(config, cors_origins, cors_methods, cors_headers,
is_production)` checks configuration compatibility and returns a list of issues
(empty when everything is OK):

- `*` origin with `allow_credentials=True` — **critical** (browsers reject it),
- `*` origin in production with `reject_wildcard_in_production=True` — **critical**,
- rate limiting disabled — warning,
- per-route limit above the global limit — warning,
- `rate_limit_requests < 10` — warning.

The CLI merges these into the audit report; you can also call it directly in code.

## Integration notes

### With `AuthMiddleware`

Rate limiting runs **before** the auth middleware. This is deliberate: login,
refresh, and OAuth endpoints are the first to be brute-forced, and the token bucket
blocks them before authentication is even attempted. Because the client key prefers
`request.state.user["sub"]` when present, authenticated users are limited by
account, while unauthenticated attackers are limited by IP.

Wire order for a fully hardened app:

```python
app = add_security_middleware(app)                 # security first
app.add_middleware(deps["middleware"], skip_paths=["/health", "/docs"])  # auth after
app = install_observability(app)                   # tracing/metrics outermost
```

### With `ObservabilityMiddleware`

Both modules attach via the standard `app.add_middleware(...)` API, so order is
just add-order. Two practical notes:

- The rate limiter and input sanitizer accept an optional `metrics_registry` and
  record `_security_rate_limit:<route>` / `_security_input_validation:block`
  events into the observability metrics registry when one is supplied — wire your
  `MetricsRegistry` through for visibility into blocked traffic.
- If you want `X-Request-ID` on `429`/`400`/`413` responses, call
  `install_observability(app)` **after** `add_security_middleware(app)` so the
  tracing middleware (added later, wraps outer) stamps the security error responses.

### Middleware ordering reference

Request flow (outermost → innermost): CORS → rate limit → request size → input
sanitization → security headers → **your app**. The headers middleware is added
first but executes last in the request path — Starlette runs middleware added
first as the outermost wrapper, so `add_security_middleware` adds components in
reverse request order to achieve the pipeline above. There is no need to reorder
anything yourself.
