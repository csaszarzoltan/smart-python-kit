"""Mock implementations for cache dependencies.

Provides an in-memory ``MockCacheBackend`` and a ``MockCacheInvalidation``
for unit testing cache-related code without a real Redis or memory backend.
"""

from __future__ import annotations

from typing import Any


class MockCacheBackend:
    """In-memory dict-based cache backend for testing.

    Implements the ``CacheBackend`` interface (get / set / delete /
    exists / clear / get_stats) using a plain dict so tests are fast
    and deterministic.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._stats: dict[str, Any] = {
            "hits": 0,
            "misses": 0,
            "keys": 0,
        }

    def get(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The cache key.

        Returns:
            The stored value, or ``None`` if the key does not exist.
        """
        value = self._store.get(key)
        if value is None and key not in self._store:
            self._stats["misses"] += 1
            return None
        self._stats["hits"] += 1
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value by key.

        Args:
            key: The cache key.
            value: The value to store.
            ttl: Optional TTL in seconds (ignored in mock).
        """
        self._store[key] = value
        self._stats["keys"] = len(self._store)

    def delete(self, key: str) -> bool:
        """Delete a single key.

        Args:
            key: The cache key to delete.

        Returns:
            ``True`` if the key existed and was deleted, ``False`` otherwise.
        """
        if key in self._store:
            del self._store[key]
            self._stats["keys"] = len(self._store)
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check whether a key exists in the cache.

        Args:
            key: The cache key.

        Returns:
            ``True`` if the key exists.
        """
        return key in self._store

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._store.clear()
        self._stats["keys"] = 0
        self._stats["hits"] = 0
        self._stats["misses"] = 0

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics (hits, misses, total keys).

        Returns:
            A dict with ``hits``, ``misses``, and ``keys`` counts.
        """
        return dict(self._stats)


class MockCacheInvalidation:
    """Mock tag/prefix-based cache invalidation for testing.

    Wraps a ``MockCacheBackend`` and provides tag tracking and
    invalidation operations.
    """

    def __init__(self, cache: MockCacheBackend) -> None:
        """Initialize with a cache backend instance.

        Args:
            cache: A ``MockCacheBackend`` instance to delegate to.
        """
        self._cache = cache
        self._tag_index: dict[str, set[str]] = {}

    def add_tags(self, key: str, tags: list[str]) -> None:
        """Associate a cache key with tags.

        Args:
            key: The cache key to tag.
            tags: List of tags to associate.
        """
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(key)

    def get_tag_keys(self, tag: str) -> set[str]:
        """Return the set of cache keys associated with a tag.

        Args:
            tag: The tag to look up.

        Returns:
            A (possibly empty) set of cache keys.
        """
        return self._tag_index.get(tag, set()).copy()

    def invalidate_tags(self, tags: list[str]) -> int:
        """Delete all cache entries matching any of the given tags.

        Args:
            tags: List of tags to invalidate.

        Returns:
            The number of keys deleted.
        """
        keys_to_delete: set[str] = set()
        for tag in tags:
            tagged = self._tag_index.pop(tag, set())
            keys_to_delete.update(tagged)

        deleted = 0
        for key in keys_to_delete:
            self._cache.delete(key)
            deleted += 1
        return deleted

    def invalidate_prefix(self, prefix: str) -> int:
        """Delete all cache entries whose key starts with the given prefix.

        Args:
            prefix: Key prefix to match.

        Returns:
            The number of keys deleted.
        """
        matching = [
            tag_key
            for tag_key in list(self._tag_index.keys())
            if tag_key.startswith(prefix)
        ]
        deleted = 0
        for tag_key in matching:
            tagged_keys = self._tag_index.pop(tag_key, set())
            for cache_key in tagged_keys:
                self._cache.delete(cache_key)
                deleted += 1
        return deleted
