"""Cache statistics dataclass for observability."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CacheStats:
    """Cache statistics for observability.

    Tracked per cache backend instance.
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    memory_bytes: int = 0  # approximate (for MemoryCache)

    @property
    def hit_rate(self) -> float:
        """Return hit rate as float 0.0-1.0."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.size = 0
        self.memory_bytes = 0


__all__ = ["CacheStats"]
