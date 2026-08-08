"""Complete security hardening example — rate limiting, headers, CORS, size limits, sanitization.

Run with:
    uvicorn examples.security_example:app --reload

Test with:
    # Health (no security events, shows security headers on every response)
    curl -i http://localhost:8000/health

    # SQL injection in a query param -> 400
    curl -i "http://localhost:8000/search?q=foo%27%20OR%201%3D1%20--"

    # XSS in the JSON body -> 400
    curl -i -X POST http://localhost:8000/echo \
        -H "Content-Type: application/json" \
        -d '{"message": "<script>alert(1)</script>"}'

    # Oversized body -> 413 (limit is 1 MiB by default)
    head -c 2000000 /dev/zero | tr '\0' 'x' > /tmp/big.txt
    curl -i -X POST http://localhost:8000/echo \
        -H "Content-Type: application/json" \
        --data-binary @/tmp/big.txt

    # Rate limit: hammer /login 6+ times -> 429 with Retry-After
    for i in $(seq 1 8); do
        curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/login
    done

    # Security headers on every response
    curl -i http://localhost:8000/health | grep -i -E "content-security|x-frame|strict-transport"
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from smartvintaawesomekit.security import (
    SecurityMiddlewareConfig,
    add_security_middleware,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# All five components are enabled by default. Tune what you need here:
config = SecurityMiddlewareConfig(
    # Rate limiting: 30 requests/minute globally,
    # 5/minute for the login endpoint (brute-force protection)
    rate_limit_requests=30,
    rate_limit_window_seconds=60,
    rate_limit_per_route={
        "/login": (5, 60),
        "/api/v1/": (300, 60),
    },
    # Explicit origins for CORS (development-friendly wildcard is the default;
    # production rejects "*" at startup)
    allowed_origins=["http://localhost:3000"],
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowed_headers=["Content-Type", "Authorization"],
    # 512 KiB body limit
    max_body_size=512 * 1024,
    # Extra sanitization patterns appended to the built-in SQLi/XSS lists
    sql_injection_patterns=[r"pg_sleep\s*\("],
    xss_patterns=[r"<iframe[^>]*>"],
)

app = FastAPI(title="Security Example", version="0.11.0")

# One-line integration — attaches CORS, rate limit, size limit, sanitization,
# and security-header middleware in the correct order.
#
# is_production is resolved from SmartConfig() automatically; pass it explicitly
# to pin the environment:
#   app = add_security_middleware(app, config, is_production=True)
app = add_security_middleware(app, config)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class EchoRequest(BaseModel):
    message: str


@app.get("/health")
async def health() -> dict[str, str]:
    """Public health check — inspect the security headers on this response."""
    return {"status": "ok"}


@app.post("/login")
async def login() -> dict[str, str]:
    """Pretend login endpoint — rate-limited to 5 requests/minute."""
    return {"token": "demo"}


@app.get("/search")
async def search(q: str) -> dict[str, str]:
    """Search endpoint — try passing SQL injection / XSS payloads as ?q=."""
    return {"query": q}


@app.post("/echo")
async def echo(req: EchoRequest) -> dict[str, str]:
    """Echo endpoint — body is sanitized; oversized bodies get 413."""
    return {"message": req.message}


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
