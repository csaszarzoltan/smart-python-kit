"""@cached decorator for caching function results."""

from __future__ import annotations

import asyncio
import functools
import hashlib
import inspect
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from smartvintaawesomekit.cache.base import CacheBackend
from smartvintaawesomekit.cache.invalidation import CacheInvalidation
from smartvintaawesomekit.cache.memory import MemoryCache

# Module-level default cache singleton — used when no explicit cache is given
_default_cache: MemoryCache | None = None

# Persistent event loop for bridging sync → async calls.
# Using ``asyncio.run()`` would close the loop after every call,
# breaking ``get_event_loop()`` for subsequent callers.
_sync_loop: asyncio.AbstractEventLoop | None = None


def _get_default_cache() -> MemoryCache:
    """Return the module-level MemoryCache singleton."""
    global _default_cache
    if _default_cache is None:
        _default_cache = MemoryCache()
    return _default_cache


def _get_sync_loop() -> asyncio.AbstractEventLoop:
    """Return a persistent event loop for sync → async bridging.

    Creates a new loop on first call; reuses it afterwards so that
    `asyncio.get_event_loop()` in downstream code continues to work.
    """
    global _sync_loop
    if _sync_loop is None or _sync_loop.is_closed():
        _sync_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_sync_loop)
    return _sync_loop


def _default_key_builder(
    func: Callable,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    prefix: str = "",
) -> str:
    """Build a deterministic cache key from function + arguments.

    Format: ``{prefix}:{module}.{qualname}:{args_hash}``

    FastAPI ``Request`` and ``Response`` objects are excluded from the
    hash because they are request-scoped and not cacheable.
    """
    # Filter out FastAPI Request/Response objects
    filtered_args = tuple(
        a
        for a in args
        if not _is_fastapi_request_response(a)
    )
    filtered_kwargs = {
        k: v
        for k, v in kwargs.items()
        if not _is_fastapi_request_response(v)
    }

    # Build a deterministic hash of the arguments
    args_repr = json.dumps(
        (filtered_args, filtered_kwargs), sort_keys=True, default=str
    )
    args_hash = hashlib.md5(args_repr.encode()).hexdigest()

    sep = ":"
    module = getattr(func, "__module__", "unknown")
    qualname = getattr(func, "__qualname__", func.__name__)
    prefix_part = f"{prefix}{sep}" if prefix else ""
    return f"{prefix_part}{module}.{qualname}:{args_hash}"


def _is_fastapi_request_response(obj: Any) -> bool:
    """Check whether *obj* is a FastAPI ``Request`` or ``Response`` instance.

    Uses a string-based check on the class name to avoid importing
    FastAPI at module level.
    """
    cls_name = type(obj).__name__
    return cls_name in ("Request", "Response")


def cached(
    ttl: int = 300,
    prefix: str = "",
    key_builder: Callable | None = None,
    tags: list[str] | None = None,
    cache: CacheBackend | None = None,
) -> Callable:
    """Decorator that caches function results.

    Works with both sync and async functions.
    For FastAPI routes: placed BETWEEN the ``@router`` decorator and the
    function definition.

    When *cache* is ``None``, uses a module-level ``MemoryCache`` singleton.

    Parameters
    ----------
    ttl : int
        Time-to-live in seconds (default 300).
    prefix : str
        Key prefix for namespace isolation.
    key_builder : callable or None
        Custom key builder ``(func, args, kwargs, prefix) -> str``.
    tags : list[str] or None
        Tags attached to the cache entry for bulk invalidation.
    cache : CacheBackend or None
        Cache backend instance. Falls back to module-level MemoryCache.
    """
    _cache: CacheBackend = cache if cache is not None else _get_default_cache()
    _key_builder = key_builder or _default_key_builder
    _invalidation: CacheInvalidation | None = (
        CacheInvalidation(_cache) if tags else None
    )

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = _key_builder(func, args, kwargs, prefix=prefix)
            cached_value = await _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)

            await _cache.set(cache_key, result, ttl=ttl)
            if _invalidation is not None and tags:
                await _invalidation.add_tags(cache_key, tags)

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = _key_builder(func, args, kwargs, prefix=prefix)
            loop = _get_sync_loop()

            cached_value = loop.run_until_complete(
                _cache.get(cache_key)
            )
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            loop.run_until_complete(
                _cache.set(cache_key, result, ttl=ttl)
            )

            if _invalidation is not None and tags:
                loop.run_until_complete(
                    _invalidation.add_tags(cache_key, tags)
                )

            return result

        return async_wrapper if is_async else sync_wrapper

    return decorator


def invalidate_cache(
    tags: list[str] | None = None,
    prefix: str | None = None,
    cache: CacheBackend | None = None,
) -> None:
    """Invalidate cache entries by tags or prefix.

    Parameters
    ----------
    tags : list[str] or None
        List of tags whose entries should be invalidated.
    prefix : str or None
        Key prefix whose entries should be invalidated.
    cache : CacheBackend or None
        Cache backend instance. Falls back to module-level MemoryCache.
    """
    _cache: CacheBackend = cache if cache is not None else _get_default_cache()
    inval = CacheInvalidation(_cache)
    loop = _get_sync_loop()

    if tags:
        loop.run_until_complete(inval.invalidate_tags(tags))
    if prefix:
        loop.run_until_complete(inval.invalidate_prefix(prefix))


__all__ = ["cached", "invalidate_cache"]
