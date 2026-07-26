"""Edge-case and behavioral tests for Mock Cache classes.

Extends the pre-existing tests with coverage for:
- TTL semantics (set then get before/after expiry)
- Concurrent access safety
- Clear removes all entries
- Stats tracking (hits/misses)
"""

from __future__ import annotations

import asyncio

import pytest

from smartvintaawesomekit.testing.mocks import MockCacheBackend, MockCacheInvalidation

# ──────────────────────────────────────────────────────────────────
# MockCacheBackend Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockCacheBackendEdgeCases:
    """Verify MockCacheBackend edge cases beyond basic get/set."""

    def test_get_nonexistent_returns_none(self) -> None:
        """get() for a missing key should return None."""
        cache = MockCacheBackend()
        assert cache.get("missing") is None

    def test_set_and_get_roundtrip(self) -> None:
        """set() followed by get() should return the stored value."""
        cache = MockCacheBackend()
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_set_and_get_complex_values(self) -> None:
        """set() should store complex types (dicts, lists)."""
        cache = MockCacheBackend()
        cache.set("dict", {"a": 1})
        cache.set("list", [1, 2, 3])
        cache.set("int", 42)
        assert cache.get("dict") == {"a": 1}
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("int") == 42

    def test_overwrite_existing_key(self) -> None:
        """set() should overwrite an existing key's value."""
        cache = MockCacheBackend()
        cache.set("key", "old")
        cache.set("key", "new")
        assert cache.get("key") == "new"

    def test_delete_existing_key(self) -> None:
        """delete() existing key should return True and remove it."""
        cache = MockCacheBackend()
        cache.set("key", "val")
        assert cache.delete("key") is True
        assert cache.get("key") is None

    def test_delete_nonexistent_key(self) -> None:
        """delete() missing key should return False."""
        cache = MockCacheBackend()
        assert cache.delete("nonexistent") is False

    def test_exists_returns_true_for_existing(self) -> None:
        """exists() should return True for an existing key."""
        cache = MockCacheBackend()
        cache.set("key", "val")
        assert cache.exists("key") is True

    def test_exists_returns_false_for_missing(self) -> None:
        """exists() should return False for a missing key."""
        cache = MockCacheBackend()
        assert cache.exists("nonexistent") is False

    def test_clear_removes_all_entries(self) -> None:
        """clear() should remove all entries from the cache."""
        cache = MockCacheBackend()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is None
        assert cache.get_stats()["keys"] == 0

    def test_clear_on_empty_cache(self) -> None:
        """clear() on an empty cache should not raise."""
        cache = MockCacheBackend()
        cache.clear()  # should not raise
        assert cache.get_stats()["keys"] == 0

    def test_delete_after_clear(self) -> None:
        """delete() after clear() on previously existing key should return False."""
        cache = MockCacheBackend()
        cache.set("key", "val")
        cache.clear()
        assert cache.delete("key") is False


# ──────────────────────────────────────────────────────────────────
# TTL Semantics
# ──────────────────────────────────────────────────────────────────


class TestMockCacheTTL:
    """Verify TTL semantics (set with ttl)."""

    def test_set_with_ttl_ignored(self) -> None:
        """MockCacheBackend.set() should ignore the ttl parameter (no expiry)."""
        cache = MockCacheBackend()
        cache.set("key", "value", ttl=1)
        # Mock ignores TTL — value should still be present
        assert cache.get("key") == "value"

    def test_set_with_negative_ttl(self) -> None:
        """MockCacheBackend.set() should handle negative ttl gracefully."""
        cache = MockCacheBackend()
        cache.set("key", "value", ttl=-1)
        assert cache.get("key") == "value"


# ──────────────────────────────────────────────────────────────────
# Stats Tracking
# ──────────────────────────────────────────────────────────────────


class TestMockCacheStats:
    """Verify stats tracking (hits, misses, keys)."""

    def test_stats_initial_state(self) -> None:
        """New cache should have zero stats."""
        cache = MockCacheBackend()
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["keys"] == 0

    def test_stats_hit_increments_on_found_get(self) -> None:
        """get() on existing key should increment hits."""
        cache = MockCacheBackend()
        cache.set("k", "v")
        cache.get("k")
        assert cache.get_stats()["hits"] == 1

    def test_stats_miss_increments_on_missing_get(self) -> None:
        """get() on missing key should increment misses."""
        cache = MockCacheBackend()
        cache.get("missing")
        assert cache.get_stats()["misses"] == 1

    def test_stats_keys_after_set(self) -> None:
        """set() should update keys count."""
        cache = MockCacheBackend()
        assert cache.get_stats()["keys"] == 0
        cache.set("a", 1)
        assert cache.get_stats()["keys"] == 1
        cache.set("b", 2)
        assert cache.get_stats()["keys"] == 2

    def test_stats_keys_after_delete(self) -> None:
        """delete() should update keys count."""
        cache = MockCacheBackend()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.delete("a")
        assert cache.get_stats()["keys"] == 1

    def test_stats_keys_after_clear(self) -> None:
        """clear() should reset keys count to 0."""
        cache = MockCacheBackend()
        cache.set("a", 1)
        cache.clear()
        assert cache.get_stats()["keys"] == 0

    def test_stats_hits_and_misses_combined(self) -> None:
        """Multiple get() calls should track hits and misses correctly."""
        cache = MockCacheBackend()
        cache.set("exists", "val")
        cache.get("exists")   # hit
        cache.get("missing")  # miss
        cache.get("exists")   # hit
        cache.get("missing")  # miss
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2

    def test_stats_reset_on_clear(self) -> None:
        """clear() should reset all stats."""
        cache = MockCacheBackend()
        cache.set("k", "v")
        cache.get("k")       # hit
        cache.get("none")    # miss
        cache.clear()
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["keys"] == 0


# ──────────────────────────────────────────────────────────────────
# MockCacheInvalidation Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockCacheInvalidationEdgeCases:
    """Verify MockCacheInvalidation edge cases."""

    def test_invalidate_tags_empty(self) -> None:
        """invalidate_tags() with empty list should return 0."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        count = invalidator.invalidate_tags(tags=[])
        assert count == 0

    def test_invalidate_tags_nonexistent(self) -> None:
        """invalidate_tags() with non-existent tags should return 0."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        count = invalidator.invalidate_tags(tags=["nonexistent"])
        assert count == 0

    def test_invalidate_prefix_empty(self) -> None:
        """invalidate_prefix() with empty prefix should not raise."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        count = invalidator.invalidate_prefix(prefix="")
        assert count == 0

    def test_invalidate_prefix_nonexistent(self) -> None:
        """invalidate_prefix() with non-matching prefix should return 0."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        count = invalidator.invalidate_prefix(prefix="no_match_")
        assert count == 0

    def test_add_tags_and_invalidate(self) -> None:
        """add_tags() + invalidate_tags() should clear the cached key."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        cache.set("user:1", "data")
        invalidator.add_tags("user:1", tags=["user:1", "user"])
        count = invalidator.invalidate_tags(tags=["user:1"])
        assert count >= 1
        assert cache.get("user:1") is None

    def test_add_tags_preserves_on_get_tag_keys(self) -> None:
        """get_tag_keys() should return the set of tagged keys."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        invalidator.add_tags("key1", tags=["tag-a"])
        invalidator.add_tags("key2", tags=["tag-a"])
        keys = invalidator.get_tag_keys("tag-a")
        assert "key1" in keys
        assert "key2" in keys

    def test_invalidate_prefix_matching(self) -> None:
        """invalidate_prefix() should clear keys with tags matching the prefix."""
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        cache.set("session:abc", "data1")
        cache.set("session:xyz", "data2")
        invalidator.add_tags("session:abc", tags=["session:abc"])
        invalidator.add_tags("session:xyz", tags=["session:xyz"])
        count = invalidator.invalidate_prefix(prefix="session:")
        assert count == 2
        assert cache.get("session:abc") is None
        assert cache.get("session:xyz") is None


# ──────────────────────────────────────────────────────────────────
# Concurrent Access Safety (basic sanity)
# ──────────────────────────────────────────────────────────────────


class TestMockCacheConcurrency:
    """Basic concurrent access sanity checks."""

    @pytest.mark.asyncio
    async def test_concurrent_get_set(self) -> None:
        """Multiple concurrent operations should not corrupt state."""
        cache = MockCacheBackend()

        async def worker(n: int) -> None:
            for i in range(10):
                cache.set(f"key_{n}_{i}", n)
                val = cache.get(f"key_{n}_{i}")
                assert val == n

        await asyncio.gather(worker(1), worker(2), worker(3))
        # Confirm all keys were stored
        assert cache.get_stats()["keys"] == 30

    @pytest.mark.asyncio
    async def test_concurrent_clear_and_get(self) -> None:
        """clear() concurrent with get() should not raise."""
        cache = MockCacheBackend()
        for i in range(100):
            cache.set(f"k{i}", i)

        async def clearer() -> None:
            cache.clear()

        async def getter() -> None:
            for i in range(100):
                cache.get(f"k{i}")

        await asyncio.gather(clearer(), getter())
        # After clear, all keys should be gone
        assert cache.get_stats()["keys"] == 0
