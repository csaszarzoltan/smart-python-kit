"""In-process metrics registry for the observability module."""
from __future__ import annotations


class MetricsRegistry:
    """Per-route request counts, latency samples, and error counts."""

    def __init__(self) -> None:
        raise NotImplementedError("MetricsRegistry is not implemented yet (RED phase)")

    def increment_request_count(self, route: str) -> None:
        raise NotImplementedError(
            "MetricsRegistry.increment_request_count is not implemented yet (RED phase)"
        )

    def increment_error_count(self, route: str) -> None:
        raise NotImplementedError(
            "MetricsRegistry.increment_error_count is not implemented yet (RED phase)"
        )

    def record_latency(self, route: str, seconds: float) -> None:
        raise NotImplementedError(
            "MetricsRegistry.record_latency is not implemented yet (RED phase)"
        )

    def request_counts(self) -> dict[str, int]:
        raise NotImplementedError(
            "MetricsRegistry.request_counts is not implemented yet (RED phase)"
        )

    def error_counts(self) -> dict[str, int]:
        raise NotImplementedError("MetricsRegistry.error_counts is not implemented yet (RED phase)")

    def latency_histograms(self) -> dict[str, list[float]]:
        raise NotImplementedError(
            "MetricsRegistry.latency_histograms is not implemented yet (RED phase)"
        )
