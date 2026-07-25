"""Tag-based and prefix-based cache invalidation."""

from __future__ import annotations

from typing import Any


class CacheInvalidation:
    """Handles tag-based and prefix-based cache invalidation.

    Tags allow grouping cache entries under labels for bulk invalidation.
    Maintains a secondary index mapping tag -> set of cache keys.
    """

    def __init__(self, cache: Any) -> None:  # CacheBackend type, avoid circular
        self._cache = cache
        self._tag_index: dict[str, set[str]] = {}

    def _ensure_init(self) -> None:
        """Lazy init for when ``__new__`` bypasses ``__init__``."""
        if not hasattr(self, "_cache"):
            self._cache = None
        if not hasattr(self, "_tag_index"):
            self._tag_index = {}

    async def add_tags(self, key: str, tags: list[str]) -> None:
        """Associate a cache key with one or more tags."""
        self._ensure_init()
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(key)

    async def get_tag_keys(self, tag: str) -> set[str]:
        """Return the set of cache keys associated with a tag."""
        self._ensure_init()
        return self._tag_index.get(tag, set()).copy()

    async def invalidate_tags(self, tags: list[str]) -> int:
        """Delete all cache entries matching any of the given tags.

        Returns the number of keys deleted.
        """
        self._ensure_init()
        keys_to_delete: set[str] = set()
        for tag in tags:
            tagged = self._tag_index.pop(tag, set())
            keys_to_delete.update(tagged)

        deleted = 0
        for key in keys_to_delete:
            if self._cache is not None and await self._cache.delete(key):
                deleted += 1
        return deleted

    async def invalidate_prefix(self, prefix: str) -> int:
        """Delete all cache entries whose key starts with the given prefix.

        Returns the number of keys deleted.
        """
        self._ensure_init()
        # Collect matching keys from tag index
        matching = [
            tag_key
            for tag_key in list(self._tag_index.keys())
            if tag_key.startswith(prefix)
        ]

        deleted = 0
        for tag_key in matching:
            tagged_keys = self._tag_index.pop(tag_key, set())
            if self._cache is not None:
                for cache_key in tagged_keys:
                    if await self._cache.delete(cache_key):
                        deleted += 1

        return deleted


__all__ = ["CacheInvalidation"]
