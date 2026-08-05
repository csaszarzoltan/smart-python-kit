"""In-process metrics registry for the observability module.

The registry is a dependency-free, thread-safe store of per-route request
counts, latency samples, and error counts. :class:`MetricsMiddleware` feeds
it from every request; application code can read the snapshots for a
``/metrics`` endpoint or periodic export.
"""
from __future__ import annotations

import threading
from collections import defaultdict


class MetricsRegistry:
    """Per-route request counts, latency samples, and error counts.

    All mutating and snapshot methods are safe to call from multiple threads
    or concurrent asyncio tasks.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._lock = threading.Lock()
        self._requests: defaultdict[str, int] = defaultdict(int)
        self._errors: defaultdict[str, int] = defaultdict(int)
        self._latency: defaultdict[str, list[float]] = defaultdict(list)

    def increment_request_count(self, route: str) -> None:
        """Increment the request counter for ``route``."""
        with self._lock:
            self._requests[route] += 1

    def increment_error_count(self, route: str) -> None:
        """Increment the error counter for ``route``."""
        with self._lock:
            self._errors[route] += 1

    def record_latency(self, route: str, seconds: float) -> None:
        """Append a latency sample (in seconds) for ``route``."""
        with self._lock:
            self._latency[route].append(seconds)

    def request_counts(self) -> dict[str, int]:
        """Return a snapshot of per-route request counts."""
        with self._lock:
            return dict(self._requests)

    def error_counts(self) -> dict[str, int]:
        """Return a snapshot of per-route error counts."""
        with self._lock:
            return dict(self._errors)

    def latency_histograms(self) -> dict[str, list[float]]:
        """Return a snapshot of per-route latency samples (seconds)."""
        with self._lock:
            return {route: list(samples) for route, samples in self._latency.items()}
