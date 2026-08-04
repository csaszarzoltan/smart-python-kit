"""TDD coverage for safe Redis cache namespacing and clear behavior."""
from __future__ import annotations

from typing import Any

import pytest

from smartvintaawesomekit.cache.redis import RedisCache


class FakeRedis:
    """Small async Redis substitute with scan support and call recording."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.flushdb_calls = 0

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str) -> None:
        self.values[key] = value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.values[key] = value

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            count += key in self.values
            self.values.pop(key, None)
        return count

    async def exists(self, key: str) -> int:
        return int(key in self.values)

    async def scan(self, cursor: int, match: str, count: int) -> tuple[int, list[str]]:
        prefix = match.removesuffix("*")
        return 0, [key for key in self.values if key.startswith(prefix)]

    async def info(self) -> dict[str, Any]:
        return {"db0": {"keys": len(self.values)}, "redis_version": "fake"}

    async def flushdb(self) -> None:
        self.flushdb_calls += 1
        self.values.clear()


@pytest.mark.asyncio
async def test_namespace_is_applied_to_all_key_operations() -> None:
    redis = FakeRedis()
    cache = RedisCache(redis, namespace="acme:prod")
    await cache.set("user:1", {"name": "Ada"})
    assert "acme:prod:user:1" in redis.values
    assert await cache.get("user:1") == {"name": "Ada"}
    assert await cache.exists("user:1") is True
    assert await cache.delete("user:1") is True
    assert "acme:prod:user:1" not in redis.values


@pytest.mark.asyncio
async def test_clear_removes_only_namespaced_keys_without_flushdb() -> None:
    redis = FakeRedis()
    cache = RedisCache(redis, namespace="service:test")
    redis.values.update({
        "service:test:a": "1",
        "service:test:b": "2",
        "other:prod:a": "3",
    })
    await cache.clear()
    assert redis.values == {"other:prod:a": "3"}
    assert redis.flushdb_calls == 0


@pytest.mark.asyncio
async def test_clear_scans_multiple_batches() -> None:
    class PagedRedis(FakeRedis):
        async def scan(self, cursor: int, match: str, count: int) -> tuple[int, list[str]]:
            if cursor == 0:
                return 1, ["app:a"]
            return 0, ["app:b"]

    redis = PagedRedis()
    redis.values.update({"app:a": "1", "app:b": "2", "other:a": "3"})
    await RedisCache(redis, namespace="app").clear()
    assert redis.values == {"other:a": "3"}


def test_namespace_validation_rejects_empty_or_wildcard_values() -> None:
    redis = FakeRedis()
    for namespace in ("", "*", "bad*namespace", " leading"):
        with pytest.raises(ValueError):
            RedisCache(redis, namespace=namespace)
