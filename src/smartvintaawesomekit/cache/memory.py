"""Thread-safe in-memory cache with TTL support."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from smartvintaawesomekit.cache.base import CacheBackend


@dataclass
class _CacheEntry:
    """Internal cache entry with metadata."""

    value: Any
    expiry: float | None  # time.monotonic() based, None = no expiry
    created_at: float
    tags: set[str] = field(default_factory=set)


class MemoryCache(CacheBackend):
    """Thread-safe in-memory cache with TTL support.

    Uses dict + threading.RLock for thread safety.
    Lazy eviction on get (checks TTL on access).
    Optional periodic cleanup via background task.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._data: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _ensure_init(self) -> None:
        """Lazy initialisation for when __new__ bypasses __init__.

        Tests that use ``MemoryCache.__new__(MemoryCache)`` skip the
        constructor, so we guarantee internal state exists here.
        """
        if not hasattr(self, "_data"):
            self.max_size = 1000
            self.default_ttl = 300
            self._data = OrderedDict()
            self._lock = threading.RLock()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    async def get(self, key: str) -> Any | None:
        self._ensure_init()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self._misses += 1
                return None

            # Lazy eviction — check TTL on access
            if entry.expiry is not None and time.monotonic() > entry.expiry:
                del self._data[key]
                self._misses += 1
                self._evictions += 1
                return None

            # Move to end for LRU ordering (most recently used)
            self._data.move_to_end(key)
            self._hits += 1
            return entry.value

    async def set(
        self, key: str, value: Any, ttl: int | None = None
    ) -> None:
        self._ensure_init()
        with self._lock:
            # Calculate expiry
            if ttl is not None and ttl <= 0:
                expiry = 0.0  # Already expired
            elif ttl is not None:
                expiry = time.monotonic() + ttl
            elif self.default_ttl > 0:
                expiry = time.monotonic() + self.default_ttl
            else:
                expiry = None  # No expiry

            # LRU eviction — pop least-recently-used when at capacity
            if key not in self._data and len(self._data) >= self.max_size:
                self._data.popitem(last=False)  # First item = LRU
                self._evictions += 1

            self._data[key] = _CacheEntry(
                value=value,
                expiry=expiry,
                created_at=time.monotonic(),
            )
            self._data.move_to_end(key)  # Mark as recently used

    async def delete(self, key: str) -> bool:
        self._ensure_init()
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        self._ensure_init()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            # Lazy eviction on exists too
            if entry.expiry is not None and time.monotonic() > entry.expiry:
                del self._data[key]
                return False
            return True

    async def clear(self) -> None:
        self._ensure_init()
        with self._lock:
            self._data.clear()

    async def get_stats(self) -> dict[str, Any]:
        self._ensure_init()
        with self._lock:
            return {
                "size": len(self._data),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
            }


__all__ = ["MemoryCache"]
