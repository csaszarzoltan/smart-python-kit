"""Redis-backed cache using redis.asyncio (optional dependency)."""

from __future__ import annotations

from typing import Any

from smartvintaawesomekit.cache.base import CacheBackend


class RedisCache(CacheBackend):
    """Redis-backed cache using redis.asyncio.

    Requires ``redis>=5.0``. An ``ImportError`` is raised with a clear
    message when ``redis`` is not installed and an operation is attempted
    that needs it.

    Usage::

        # Option 1 — from URL (creates connection pool)
        cache = RedisCache.from_url("redis://localhost:6379")

        # Option 2 — pass pre-configured redis client
        from redis.asyncio import Redis
        client = Redis.from_url("redis://localhost:6379")
        cache = RedisCache(client)
    """

    def __init__(self, redis_client: Any, pool_size: int = 10, namespace: str = "smartvinta") -> None:
        """Initialize a namespaced Redis backend safe for shared databases."""
        if not namespace or namespace != namespace.strip() or "*" in namespace:
            raise ValueError("namespace must be non-empty, trimmed, and contain no wildcards")
        self._redis = redis_client
        self._pool_size = pool_size
        self._namespace = namespace.rstrip(":")
        self._hits = 0
        self._misses = 0

    def _ensure_init(self) -> None:
        """Lazy init for when ``__new__`` bypasses ``__init__``."""
        if not hasattr(self, "_redis"):
            self._redis = None
            self._pool_size = 10
            self._hits = 0
            self._misses = 0
            self._fallback: dict[str, Any] = {}
            self._namespace = "smartvinta"

    @classmethod
    def from_url(cls, url: str, pool_size: int = 10, namespace: str = "smartvinta") -> RedisCache:
        """Create a ``RedisCache`` from a Redis connection URL.

        Parameters
        ----------
        url : str
            Redis connection URL (e.g. ``redis://localhost:6379/0``).
        pool_size : int
            Connection pool size (default 10).

        Returns
        -------
        RedisCache
        """
        try:
            from redis.asyncio import Redis  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "redis package is required for RedisCache. "
                "Install it with: pip install smartvintaawesomekit[redis]"
            ) from exc

        client = Redis.from_url(url, max_connections=pool_size)
        return cls(redis_client=client, pool_size=pool_size, namespace=namespace)

    def _key(self, key: str) -> str:
        """Return a key scoped to this application namespace."""
        return f"{self._namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        self._ensure_init()
        key = self._key(key)
        if self._redis is None:
            value = self._fallback.get(key)
            if value is None:
                self._misses += 1
                return None
            self._hits += 1
            return value
        value = await self._redis.get(key)
        if value is None:
            self._misses += 1
            return None
        self._hits += 1
        return _deserialize(value)

    async def set(
        self, key: str, value: Any, ttl: int | None = None
    ) -> None:
        self._ensure_init()
        key = self._key(key)
        if self._redis is None:
            self._fallback[key] = value
            return
        serialized = _serialize(value)
        if ttl is not None:
            await self._redis.setex(key, ttl, serialized)
        else:
            await self._redis.set(key, serialized)

    async def delete(self, key: str) -> bool:
        self._ensure_init()
        key = self._key(key)
        if self._redis is None:
            return False
        result = await self._redis.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        self._ensure_init()
        key = self._key(key)
        if self._redis is None:
            return False
        result = await self._redis.exists(key)
        return result > 0

    async def clear(self) -> None:
        self._ensure_init()
        if self._redis is None:
            self._fallback.clear()
            return
        cursor = 0
        pattern = f"{self._namespace}:*"
        while True:
            cursor, keys = await self._redis.scan(cursor, match=pattern, count=500)
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break

    async def get_stats(self) -> dict[str, Any]:
        self._ensure_init()
        stats: dict[str, Any] = {
            "size": 0,
            "hits": self._hits,
            "misses": self._misses,
        }
        if self._redis is not None:
            try:
                info = await self._redis.info()
                stats["size"] = info.get("db0", {}).get("keys", 0)
                stats["redis_version"] = info.get("redis_version", "")
            except Exception:
                pass
        return stats


def _serialize(value: Any) -> str:
    """Serialize a Python object to JSON string for Redis storage."""
    import json
    return json.dumps(value, default=str)


def _deserialize(value: str | bytes) -> Any:
    """Deserialize a JSON string from Redis storage back to Python object."""
    import json
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


__all__ = ["RedisCache"]
