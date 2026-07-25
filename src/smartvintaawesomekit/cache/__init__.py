"""Caching module — in-memory + optional Redis cache backend."""

from smartvintaawesomekit.cache.base import CacheBackend
from smartvintaawesomekit.cache.config import CacheConfig
from smartvintaawesomekit.cache.decorator import cached, invalidate_cache
from smartvintaawesomekit.cache.invalidation import CacheInvalidation
from smartvintaawesomekit.cache.memory import MemoryCache
from smartvintaawesomekit.cache.stats import CacheStats

__all__ = [
    "CacheBackend",
    "CacheConfig",
    "CacheInvalidation",
    "CacheStats",
    "MemoryCache",
    "cached",
    "invalidate_cache",
]
