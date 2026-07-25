"""Cache configuration — loaded from CACHE_* env vars."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class CacheConfig(BaseSettings):
    """Cache module configuration — loaded from CACHE_* env vars."""

    default_ttl: int = Field(default=300, description="Default TTL in seconds")
    max_size: int = Field(default=1000, description="Max cache entries (memory backend)")
    cleanup_interval: int = Field(default=60, description="Cleanup sweep interval in seconds")
    redis_url: str = Field(default="", description="Redis connection URL")
    redis_pool_size: int = Field(default=10, description="Redis connection pool size")
    enable_stats: bool = Field(default=True, description="Enable cache statistics collection")
    key_prefix_separator: str = Field(default=":", description="Separator for key namespacing")

    model_config = {"env_prefix": "CACHE_"}


__all__ = ["CacheConfig"]
