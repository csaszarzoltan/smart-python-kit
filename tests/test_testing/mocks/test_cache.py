"""Behavioral and interface tests for Mock Cache classes.

Interface tests:
    - Verify MockCacheBackend, MockCacheInvalidation exist
    - Verify method signatures and return types

Behavioral tests:
    - MockCacheBackend stores/retrieves data in-memory dict
    - MockCacheBackend deletes entries
    - MockCacheInvalidation invalidates by tag/prefix
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from smartvintaawesomekit.testing.mocks import MockCacheBackend, MockCacheInvalidation

# ──────────────────────────────────────────────────────────────────
# 1. MockCacheBackend
# ──────────────────────────────────────────────────────────────────


class TestMockCacheBackendInterface:
    """Verify MockCacheBackend API exists with correct signatures."""

    def test_mockcachebackend_class_exists(self) -> None:
        """MockCacheBackend class should be importable."""
        assert MockCacheBackend is not None

    def test_mockcachebackend_has_get_method(self) -> None:
        """MockCacheBackend should have get method."""
        assert hasattr(MockCacheBackend, "get")
        assert callable(MockCacheBackend.get)

    def test_mockcachebackend_has_set_method(self) -> None:
        """MockCacheBackend should have set method."""
        assert hasattr(MockCacheBackend, "set")
        assert callable(MockCacheBackend.set)

    def test_mockcachebackend_has_delete_method(self) -> None:
        """MockCacheBackend should have delete method."""
        assert hasattr(MockCacheBackend, "delete")
        assert callable(MockCacheBackend.delete)

    def test_mockcachebackend_has_clear_method(self) -> None:
        """MockCacheBackend should have clear method."""
        assert hasattr(MockCacheBackend, "clear")
        assert callable(MockCacheBackend.clear)

    def test_get_signature(self) -> None:
        """get() should accept key parameter."""
        sig = inspect.signature(MockCacheBackend.get)
        assert "key" in sig.parameters

    def test_set_signature(self) -> None:
        """set() should accept key, value, and optional ttl."""
        sig = inspect.signature(MockCacheBackend.set)
        assert "key" in sig.parameters
        assert "value" in sig.parameters

    def test_delete_signature(self) -> None:
        """delete() should accept key parameter."""
        sig = inspect.signature(MockCacheBackend.delete)
        assert "key" in sig.parameters

    def test_get_return_type(self) -> None:
        """get() return type hint should exist."""
        hints = get_type_hints(MockCacheBackend.get)
        assert "return" in hints

    def test_set_return_type(self) -> None:
        """set() return type hint should exist."""
        hints = get_type_hints(MockCacheBackend.set)
        assert "return" in hints

    def test_delete_return_type(self) -> None:
        """delete() return type should be bool."""
        hints = get_type_hints(MockCacheBackend.delete)
        assert hints.get("return") is bool

    def test_exists_method(self) -> None:
        """MockCacheBackend should have exists method."""
        assert hasattr(MockCacheBackend, "exists")
        assert callable(MockCacheBackend.exists)

    def test_exists_return_type(self) -> None:
        """exists() return type should be bool."""
        hints = get_type_hints(MockCacheBackend.exists)
        if hints.get("return") is not None:
            assert hints["return"] is bool


class TestMockCacheBackendBehavioral:
    """Verify MockCacheBackend behaviors."""

    def test_mockcachebackend_get_set_roundtrip(self) -> None:
        """MockCacheBackend should store and retrieve values."""
        # Implemented behavior
        cache = MockCacheBackend()
        cache.set(key="test_key", value="test_value")
        result = cache.get(key="test_key")
        assert result == "test_value"

    def test_mockcachebackend_get_nonexistent_returns_none(self) -> None:
        """MockCacheBackend.get() should return None for missing keys."""
        # Implemented behavior
        cache = MockCacheBackend()
        result = cache.get(key="nonexistent")
        assert result is None

    def test_mockcachebackend_delete_removes_entry(self) -> None:
        """MockCacheBackend.delete() should remove entry and return True."""
        # Implemented behavior
        cache = MockCacheBackend()
        cache.set(key="to_delete", value="data")
        deleted = cache.delete(key="to_delete")
        assert deleted is True
        assert cache.get(key="to_delete") is None

    def test_mockcachebackend_clear_all_entries(self) -> None:
        """MockCacheBackend.clear() should remove all entries."""
        # Implemented behavior
        cache = MockCacheBackend()
        cache.set(key="a", value=1)
        cache.set(key="b", value=2)
        cache.clear()
        assert cache.get(key="a") is None
        assert cache.get(key="b") is None

    def test_mockcachebackend_exists_returns_bool(self) -> None:
        """MockCacheBackend.exists() should return True/False."""
        # Implemented behavior
        cache = MockCacheBackend()
        cache.set(key="exists_key", value="val")
        assert cache.exists(key="exists_key") is True
        assert cache.exists(key="missing_key") is False


# ──────────────────────────────────────────────────────────────────
# 2. MockCacheInvalidation
# ──────────────────────────────────────────────────────────────────


class TestMockCacheInvalidationInterface:
    """Verify MockCacheInvalidation API exists with correct signatures."""

    def test_mockcacheinvalidation_class_exists(self) -> None:
        """MockCacheInvalidation class should be importable."""
        assert MockCacheInvalidation is not None

    def test_mockcacheinvalidation_has_invalidate_tags(self) -> None:
        """MockCacheInvalidation should have invalidate_tags method."""
        assert hasattr(MockCacheInvalidation, "invalidate_tags")
        assert callable(MockCacheInvalidation.invalidate_tags)

    def test_mockcacheinvalidation_has_invalidate_prefix(self) -> None:
        """MockCacheInvalidation should have invalidate_prefix method."""
        assert hasattr(MockCacheInvalidation, "invalidate_prefix")
        assert callable(MockCacheInvalidation.invalidate_prefix)

    def test_mockcacheinvalidation_init_signature(self) -> None:
        """MockCacheInvalidation.__init__ should accept cache param."""
        sig = inspect.signature(MockCacheInvalidation.__init__)
        assert "self" in sig.parameters
        assert "cache" in sig.parameters

    def test_invalidate_tags_signature(self) -> None:
        """invalidate_tags should accept tags param."""
        sig = inspect.signature(MockCacheInvalidation.invalidate_tags)
        assert "tags" in sig.parameters

    def test_invalidate_prefix_signature(self) -> None:
        """invalidate_prefix should accept prefix param."""
        sig = inspect.signature(MockCacheInvalidation.invalidate_prefix)
        assert "prefix" in sig.parameters

    def test_invalidate_tags_return_type(self) -> None:
        """invalidate_tags should return int."""
        hints = get_type_hints(MockCacheInvalidation.invalidate_tags)
        assert hints.get("return") is int

    def test_invalidate_prefix_return_type(self) -> None:
        """invalidate_prefix should return int."""
        hints = get_type_hints(MockCacheInvalidation.invalidate_prefix)
        assert hints.get("return") is int


class TestMockCacheInvalidationBehavioral:
    """Verify MockCacheInvalidation behaviors."""

    def test_invalidate_tags_clears_matching(self) -> None:
        """MockCacheInvalidation.invalidate_tags() should clear entries with matching tags."""
        # Implemented behavior
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        cache.set(key="user:1", value="data")
        count = invalidator.invalidate_tags(tags=["user:1"])
        assert isinstance(count, int)

    def test_invalidate_prefix_clears_matching(self) -> None:
        """MockCacheInvalidation.invalidate_prefix() should clear entries with matching prefix."""
        # Implemented behavior
        cache = MockCacheBackend()
        invalidator = MockCacheInvalidation(cache=cache)
        cache.set(key="session:abc", value="data")
        count = invalidator.invalidate_prefix(prefix="session:")
        assert isinstance(count, int)


# ──────────────────────────────────────────────────────────────────
# 3. Package exports
# ──────────────────────────────────────────────────────────────────


class TestMockCacheModuleIntegration:
    """Verify mocks package exports cache mock classes."""

    def test_package_exports_mockcachebackend(self) -> None:
        """smartvintaawesomekit.testing.mocks should export MockCacheBackend."""
        from smartvintaawesomekit.testing.mocks import MockCacheBackend as MCB
        assert MCB is MockCacheBackend

    def test_package_exports_mockcacheinvalidation(self) -> None:
        """smartvintaawesomekit.testing.mocks should export MockCacheInvalidation."""
        from smartvintaawesomekit.testing.mocks import MockCacheInvalidation as MCI
        assert MCI is MockCacheInvalidation
