# Caching Module

In-memory and optional Redis caching for FastAPI applications — TTL-based key-value store, route-level caching decorator, tag/prefix-based invalidation, and observability statistics.

## Installation

The caching module is included in `smartvintaawesomekit`. No additional core dependencies are required for the in-memory backend:

```bash
pip install smartvintaawesomekit
```

For the Redis backend, install the optional `[redis]` extra:

```bash
pip install smartvintaawesomekit[redis]
```

**Core dependencies:** none added — in-memory cache uses Python stdlib (`threading`, `time`, `collections.OrderedDict`).

**Optional dependency:** `redis>=5.0` for `RedisCache`.

## Configuration

All caching settings are loaded from environment variables prefixed with `CACHE_`. Create an `.env` file or export these before starting your app:

```bash
# Optional (defaults shown)
CACHE_DEFAULT_TTL=300
CACHE_MAX_SIZE=1000
CACHE_CLEANUP_INTERVAL=60
CACHE_ENABLE_STATS=true
CACHE_KEY_PREFIX_SEPARATOR=:

# Redis connection (only needed for RedisCache)
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_REDIS_POOL_SIZE=10
```

The `CacheConfig` class uses `pydantic-settings` with `env_prefix="CACHE_"`:

```python
from smartvintaawesomekit.cache import CacheConfig

config = CacheConfig()  # reads from environment
print(config.default_ttl)             # default: 300
print(config.max_size)                # default: 1000
print(config.redis_url)               # default: "" (empty = Redis disabled)
print(config.enable_stats)            # default: True
```

| Field | Env Var | Default | Description |
|-------|---------|---------|-------------|
| `default_ttl` | `CACHE_DEFAULT_TTL` | `300` | Default TTL in seconds |
| `max_size` | `CACHE_MAX_SIZE` | `1000` | Max cache entries (memory backend) |
| `cleanup_interval` | `CACHE_CLEANUP_INTERVAL` | `60` | Cleanup sweep interval in seconds |
| `redis_url` | `CACHE_REDIS_URL` | `""` | Redis connection URL (empty = disabled) |
| `redis_pool_size` | `CACHE_REDIS_POOL_SIZE` | `10` | Redis connection pool size |
| `enable_stats` | `CACHE_ENABLE_STATS` | `true` | Enable cache statistics collection |
| `key_prefix_separator` | `CACHE_KEY_PREFIX_SEPARATOR` | `:` | Separator for key namespacing |

## Quick Start

Wire a basic in-memory cache into a FastAPI app:

```python
from fastapi import FastAPI
from smartvintaawesomekit.cache import MemoryCache

app = FastAPI()
cache = MemoryCache(max_size=1000, default_ttl=300)

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    cached = await cache.get(f"item:{item_id}")
    if cached is not None:
        return {"source": "cache", "data": cached}

    # Expensive lookup
    data = {"id": item_id, "name": "Sample Item", "price": 9.99}
    await cache.set(f"item:{item_id}", data, ttl=60)
    return {"source": "db", "data": data}
```

## Backends

### In-Memory Cache (Default)

`MemoryCache` — thread-safe, TTL-aware, LRU-evicting dict-based cache. Uses `threading.RLock` for concurrent access safety and `time.monotonic()` for TTL expiry (immune to system clock changes).

```python
from smartvintaawesomekit.cache import MemoryCache

cache = MemoryCache(max_size=1000, default_ttl=300)

# Set with custom TTL (overrides default_ttl)
await cache.set("user:42", {"name": "Alice", "role": "admin"}, ttl=60)

# Get — returns None if expired or missing
user = await cache.get("user:42")
assert user["name"] == "Alice"

# Exists check
assert await cache.exists("user:42")

# Delete
await cache.delete("user:42")

# Clear all entries
await cache.clear()

# Stats
stats = await cache.get_stats()
```

**Key behaviors:**
- **Lazy eviction** — expired entries are removed on `get()` / `exists()` access
- **LRU eviction** — when `max_size` is reached, the least-recently-used entry is evicted before inserting a new one
- **Thread safety** — all operations acquire a reentrant lock (`threading.RLock`)

### Redis Cache (Optional)

`RedisCache` — async Redis-backed cache using `redis.asyncio`. Requires the `[redis]` extra. Supports the same interface as `MemoryCache`.

```python
from smartvintaawesomekit.cache import CacheConfig
from smartvintaawesomekit.cache.redis import RedisCache

config = CacheConfig()
cache = RedisCache.from_url(
    config.redis_url or "redis://localhost:6379/0",
    pool_size=config.redis_pool_size,
    namespace="myapp:development",
)

# Same interface as MemoryCache
await cache.set("key", {"nested": "value"}, ttl=300)
value = await cache.get("key")

# Or pass an existing redis client
from redis.asyncio import Redis

client = Redis.from_url("redis://localhost:6379/0")
cache = RedisCache(redis_client=client)
```

**Key behaviors:**
- **Lazy import** — `ImportError` with a clear message is raised only when instantiated without `redis` installed
- **JSON serialization** — values are serialized with `json.dumps` / `json.loads`
- **Connection pool** — uses `redis.asyncio.Redis.from_url()` with configurable `max_connections`

## Route Caching

The `@cached` decorator caches FastAPI route responses. Place it between the `@app.get` (or `@router`) decorator and the function definition.

### Basic Usage

```python
from fastapi import FastAPI
from smartvintaawesomekit.cache import cached

app = FastAPI()

@app.get("/users/{user_id}")
@cached(ttl=60)
async def get_user(user_id: int):
    # Expensive DB call — result cached for 60 seconds
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}
```

### Prefix-Based Key Namespacing

Use the `prefix` parameter to isolate cache keys by domain:

```python
@app.get("/products/{product_id}")
@cached(ttl=300, prefix="products")
async def get_product(product_id: int):
    return {"id": product_id, "name": "Widget"}
```

### Tag-Based Caching

Tags group cache entries for bulk invalidation later:

```python
@app.get("/users/{user_id}")
@cached(ttl=60, tags=["user-data"])
async def get_user(user_id: int):
    return {"id": user_id, "name": "Alice"}
```

### Cache Busting

Invalidate cached responses programmatically using `invalidate_cache`:

```python
from smartvintaawesomekit.cache import cached, invalidate_cache

@app.post("/users/{user_id}")
async def update_user(user_id: int, name: str):
    # Update the database ...
    # Then invalidate the cached entry for this user
    invalidate_cache(tags=[f"user:{user_id}"])
    return {"updated": True}
```

**Decorator parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl` | `int` | `300` | Time-to-live in seconds |
| `prefix` | `str` | `""` | Key prefix for namespace isolation |
| `key_builder` | `callable` | `None` | Custom key builder `(func, args, kwargs, prefix) -> str` |
| `tags` | `list[str]` | `None` | Tags attached to the cache entry for bulk invalidation |
| `cache` | `CacheBackend` | `None` | Cache backend instance (default: module-level `MemoryCache` singleton) |

**Key behavior:**
- Works with **both sync and async** functions (auto-detected via `inspect.iscoroutinefunction`)
- FastAPI `Request` / `Response` objects are **automatically excluded** from key computation
- Default key format: `{prefix}:{module}.{qualname}:{args_hash}` (MD5 of JSON-serialized args)

## Cache Invalidation

`CacheInvalidation` provides tag-based and prefix-based bulk invalidation.

### Tag-Based Invalidation

```python
from smartvintaawesomekit.cache import MemoryCache, CacheInvalidation

cache = MemoryCache()
inval = CacheInvalidation(cache)

# Store data with tags
await cache.set("user:42", user_data, ttl=300)
await inval.add_tags("user:42", ["user:42", "role:admin", "org:acme"])

# Later — invalidate all entries tagged with "user:42"
deleted = await inval.invalidate_tags(["user:42"])
print(f"Invalidated {deleted} entries")

# Get tag keys (without deleting)
keys = await inval.get_tag_keys("role:admin")
```

### Prefix-Based Invalidation

```python
# Invalidate all cache entries whose key starts with a prefix
deleted = await inval.invalidate_prefix("user:")
print(f"Invalidated {deleted} entries")
```

### With Route Decorator (FastAPI)

The `@cached` decorator with tags automatically registers tag associations. Use `invalidate_cache()` (sync helper) to bust on write endpoints:

```python
from smartvintaawesomekit.cache import cached, invalidate_cache

@app.get("/posts/{post_id}")
@cached(ttl=120, tags=["posts"])
async def get_post(post_id: int):
    return {"id": post_id, "title": "Hello"}

@app.put("/posts/{post_id}")
async def update_post(post_id: int):
    # Update DB ...
    invalidate_cache(tags=["posts"])
    return {"ok": True}
```

## Statistics

`CacheStats` provides observability into cache effectiveness.

```python
from smartvintaawesomekit.cache import MemoryCache, CacheStats

cache = MemoryCache(max_size=100, default_ttl=60)

# After some get/set operations
raw = await cache.get_stats()
stats = CacheStats(**raw)

print(f"Size: {stats.size}")
print(f"Hits: {stats.hits}")
print(f"Misses: {stats.misses}")
print(f"Evictions: {stats.evictions}")
print(f"Hit rate: {stats.hit_rate:.1%}")  # 0.0 - 1.0

# Reset counters without affecting cached data
stats.reset()
```

**`CacheStats` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `hits` | `int` | Number of successful cache lookups |
| `misses` | `int` | Number of cache misses |
| `evictions` | `int` | Number of evicted entries |
| `size` | `int` | Current number of entries |
| `memory_bytes` | `int` | Approximate memory usage (MemoryCache only) |

**`hit_rate` property:** returns `0.0` when no lookups have been performed (avoids zero-division).

## API Reference

### `smartvintaawesomekit.cache`

**Top-level imports:**

```python
from smartvintaawesomekit.cache import (
    CacheBackend,       # Abstract base class
    CacheConfig,        # Pydantic-settings config
    CacheInvalidation,  # Tag/prefix invalidation
    CacheStats,         # Observability dataclass
    MemoryCache,        # Thread-safe in-memory backend
    cached,             # Route decorator
    invalidate_cache,   # Sync cache busting helper
)
```

### `CacheBackend` (Abstract Base)

Abstract interface all cache backends must implement.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get` | `(key: str) -> Any \| None` | Cached value or `None` | Retrieve a value by key |
| `set` | `(key: str, value: Any, ttl: int \| None = None) -> None` | — | Store a value with optional TTL |
| `delete` | `(key: str) -> bool` | `True` if deleted | Remove a single entry |
| `exists` | `(key: str) -> bool` | `True` if exists | Check key existence |
| `clear` | `() -> None` | — | Remove all entries |
| `get_stats` | `() -> dict[str, Any]` | Stats dict | Get runtime statistics |

### `CacheConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_ttl` | `int` | `300` | Default TTL in seconds |
| `max_size` | `int` | `1000` | Max cache entries (memory backend) |
| `cleanup_interval` | `int` | `60` | Cleanup sweep interval in seconds |
| `redis_url` | `str` | `""` | Redis connection URL |
| `redis_pool_size` | `int` | `10` | Redis connection pool size |
| `enable_stats` | `bool` | `True` | Enable cache statistics collection |
| `key_prefix_separator` | `str` | `":"` | Separator for key namespacing |

### `MemoryCache`

Constructor: `MemoryCache(max_size: int = 1000, default_ttl: int = 300)`

Implements `CacheBackend`. Thread-safe via `threading.RLock`. LRU eviction when `max_size` is reached.

### `RedisCache`

Constructor: `RedisCache(redis_client: Redis, pool_size: int = 10)`

Factory: `RedisCache.from_url(url: str, pool_size: int = 10) -> RedisCache`

Implements `CacheBackend`. Requires `redis>=5.0`. JSON serialization for values.

### `cached`

Decorator: `cached(ttl=300, prefix="", key_builder=None, tags=None, cache=None)`

Works with sync and async functions. When `cache` is `None`, uses a module-level `MemoryCache` singleton.

### `invalidate_cache`

Function: `invalidate_cache(tags=None, prefix=None, cache=None)`

Synchronous helper for cache busting from FastAPI route handlers. Internally bridges to async via a persistent event loop.

### `CacheInvalidation`

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `add_tags` | `(key: str, tags: list[str]) -> None` | — | Associate tags with a cache key |
| `get_tag_keys` | `(tag: str) -> set[str]` | Set of keys | Look up keys by tag |
| `invalidate_tags` | `(tags: list[str]) -> int` | Count deleted | Bulk invalidate by tags |
| `invalidate_prefix` | `(prefix: str) -> int` | Count deleted | Bulk invalidate by key prefix |

### `CacheStats`

Dataclass with fields `hits`, `misses`, `evictions`, `size`, `memory_bytes`.

| Member | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `hit_rate` | (property) | `float` | Hit rate 0.0–1.0 |
| `reset` | `() -> None` | — | Reset all counters to zero |

## Examples

### Basic In-Memory Cache

```python
from smartvintaawesomekit.cache import MemoryCache

cache = MemoryCache(max_size=1000, default_ttl=300)

await cache.set("greeting", "Hello, World!", ttl=60)
value = await cache.get("greeting")
print(value)  # "Hello, World!"

await cache.delete("greeting")
assert await cache.get("greeting") is None
```

### Redis Cache

```python
from smartvintaawesomekit.cache.redis import RedisCache

# Requires: pip install smartvintaawesomekit[redis]
cache = RedisCache.from_url("redis://localhost:6379/0")

await cache.set("counter", 42, ttl=3600)
value = await cache.get("counter")
print(value)  # 42

stats = await cache.get_stats()
print(stats)
```

### Cache Stats Observability

```python
from smartvintaawesomekit.cache import MemoryCache, CacheStats

cache = MemoryCache()

await cache.set("a", 1, ttl=10)
await cache.get("a")    # hit
await cache.get("a")    # hit
await cache.get("b")    # miss

raw = await cache.get_stats()
stats = CacheStats(**raw)
print(f"Hit rate: {stats.hit_rate:.0%}")  # 67%
```

## Full Example

See `examples/caching_example.py` for a complete runnable FastAPI application demonstrating in-memory caching, the `@cached` decorator with tags, cache invalidation on write endpoints, and a cache stats endpoint.
