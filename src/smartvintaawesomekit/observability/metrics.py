"""In-process metrics registry for the observability module.

The registry is a dependency-free, thread-safe store of per-route request
counts, error counts, and latency histograms. :class:`MetricsMiddleware` feeds
it from every request; application code can read the snapshots for a
``/metrics`` endpoint or periodic export.

Storage is bounded by design:

- latency samples are aggregated into a fixed set of log-scaled histogram
  buckets (never a growing list), so N samples cost the same as 1;
- the number of distinct route keys is capped at :data:`MetricsRegistry.MAX_ROUTES`;
  routes beyond the cap roll up into :data:`MetricsRegistry.OTHER_ROUTE`, so
  attacker-controlled unique paths cannot grow the registry without bound.
"""
from __future__ import annotations

import bisect
import threading
from collections import defaultdict
from typing import Final

#: Upper bounds (seconds) of the latency histogram buckets. A sample of ``s``
#: seconds is counted in the first bucket whose bound is ``>= s``; the final
#: ``inf`` bound is the catch-all for the slowest samples. Counts are
#: per-bucket (non-cumulative): ``counts[i]`` is the number of samples in
#: bucket ``i``, i.e. latency in ``(buckets[i-1], buckets[i]]`` seconds, with
#: the first bucket holding ``s <= buckets[0]``.
HISTOGRAM_BUCKETS: Final[tuple[float, ...]] = (
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    float("inf"),
)


def _empty_histogram() -> list[int]:
    """Return a zeroed bucket-count list aligned with HISTOGRAM_BUCKETS."""
    return [0] * len(HISTOGRAM_BUCKETS)


class MetricsRegistry:
    """Per-route request counts, latency histograms, and error counts.

    All mutating and snapshot methods are safe to call from multiple threads
    or concurrent asyncio tasks.
    """

    #: Maximum number of distinct route keys tracked. New routes beyond this
    #: cap roll up into :attr:`OTHER_ROUTE`.
    MAX_ROUTES: Final[int] = 1000

    #: Catch-all key for routes beyond :attr:`MAX_ROUTES`.
    OTHER_ROUTE: Final[str] = "_other"

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._lock = threading.Lock()
        self._requests: defaultdict[str, int] = defaultdict(int)
        self._errors: defaultdict[str, int] = defaultdict(int)
        self._latency: defaultdict[str, list[int]] = defaultdict(_empty_histogram)
        self._known_routes: set[str] = set()

    def histogram_buckets(self) -> tuple[float, ...]:
        """Return the latency histogram bucket upper bounds (seconds).

        The returned tuple is aligned with the per-route count lists from
        :meth:`latency_histograms`; the final element is ``inf``.
        """
        return HISTOGRAM_BUCKETS

    def _coerce_route(self, route: str) -> str:
        """Roll new routes into :attr:`OTHER_ROUTE` once the cap is reached.

        Must be called while holding ``self._lock``.
        """
        if route in self._known_routes:
            return route
        if len(self._known_routes) >= self.MAX_ROUTES:
            return self.OTHER_ROUTE
        self._known_routes.add(route)
        return route

    def increment_request_count(self, route: str) -> None:
        """Increment the request counter for ``route``."""
        with self._lock:
            self._requests[self._coerce_route(route)] += 1

    def increment_error_count(self, route: str) -> None:
        """Increment the error counter for ``route``."""
        with self._lock:
            self._errors[self._coerce_route(route)] += 1

    def record_latency(self, route: str, seconds: float) -> None:
        """Record a latency sample (seconds) into a fixed histogram bucket.

        Storage for ``route`` is constant regardless of how many samples are
        recorded — samples are aggregated, never appended to a list.
        """
        with self._lock:
            key = self._coerce_route(route)
            bucket = bisect.bisect_left(HISTOGRAM_BUCKETS, seconds)
            self._latency[key][bucket] += 1

    def request_counts(self) -> dict[str, int]:
        """Return a snapshot of per-route request counts."""
        with self._lock:
            return dict(self._requests)

    def error_counts(self) -> dict[str, int]:
        """Return a snapshot of per-route error counts."""
        with self._lock:
            return dict(self._errors)

    def latency_histograms(self) -> dict[str, list[int]]:
        """Return a snapshot of per-route latency histogram bucket counts.

        Each value is a list of counts aligned with :meth:`histogram_buckets`:
        ``counts[i]`` is the number of samples in bucket ``i``, i.e. latency
        in ``(buckets[i-1], buckets[i]]`` seconds, with the first bucket
        holding ``s <= buckets[0]``. Counts are per-bucket (non-cumulative).
        Per-route storage is fixed regardless of how many samples were
        recorded.
        """
        with self._lock:
            return {route: list(counts) for route, counts in self._latency.items()}
