"""Complete caching example — in-memory cache, @cached decorator, tag-based invalidation, stats.

Run with:
    uvicorn examples.caching_example:app --reload

Test with:
    # List items (cached for 30s)
    curl http://localhost:8000/items

    # Get single item (cached for 10s)
    curl http://localhost:8000/items/1

    # Create item (invalidates list cache)
    curl -X POST http://localhost:8000/items \
        -H "Content-Type: application/json" \
        -d '{"name": "Widget", "price": 9.99}'

    # Update item (invalidates both list + single caches)
    curl -X PUT http://localhost:8000/items/1 \
        -H "Content-Type: application/json" \
        -d '{"name": "Widget Pro", "price": 19.99}'

    # Delete item (invalidates cache)
    curl -X DELETE http://localhost:8000/items/1

    # Cache stats
    curl http://localhost:8000/cache/stats
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from smartvintaawesomekit.cache import (
    CacheStats,
    MemoryCache,
    cached,
    invalidate_cache,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = FastAPI(title="Caching Example", version="0.3.0")

# Create a dedicated cache backend shared across the app
# (the @cached decorator uses its own module-level singleton by default,
#  but passing it explicitly is clearer for shared invalidation)
cache = MemoryCache(max_size=500, default_ttl=300)

# In-memory "database"
_items: dict[int, dict] = {
    1: {"id": 1, "name": "Laptop", "price": 1299.99},
    2: {"id": 2, "name": "Mouse", "price": 29.99},
    3: {"id": 3, "name": "Keyboard", "price": 89.99},
}
_next_id = 4

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ItemCreate(BaseModel):
    name: str
    price: float


class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float


# ---------------------------------------------------------------------------
# Routes — cache stats (public)
# ---------------------------------------------------------------------------


@app.get("/cache/stats")
async def get_cache_stats() -> dict:
    """Return cache performance statistics and raw counters."""
    raw = await cache.get_stats()
    stats = CacheStats(**raw)
    return {
        "size": stats.size,
        "hits": stats.hits,
        "misses": stats.misses,
        "evictions": stats.evictions,
        "hit_rate": round(stats.hit_rate, 4),
    }


# ---------------------------------------------------------------------------
# Routes — items (cached reads, invalidating writes)
# ---------------------------------------------------------------------------


@app.get("/items", response_model=list[ItemResponse])
@cached(ttl=30, tags=["items:list"], cache=cache)
async def list_items() -> list[ItemResponse]:
    """Return all items. Cached for 30 seconds."""
    return [ItemResponse(**item) for item in _items.values()]


@app.get("/items/{item_id}", response_model=ItemResponse)
@cached(ttl=10, tags=["items:detail"], cache=cache)
async def get_item(item_id: int) -> ItemResponse:
    """Return a single item by ID. Cached for 10 seconds."""
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse(**item)


@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(req: ItemCreate) -> ItemResponse:
    """Create a new item, then invalidate the list cache."""
    global _next_id  # noqa: PLW0603

    item = {"id": _next_id, "name": req.name, "price": req.price}
    _items[_next_id] = item
    _next_id += 1

    # Invalidate the cached item list so next GET /items is fresh
    invalidate_cache(tags=["items:list"], cache=cache)

    return ItemResponse(**item)


@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, req: ItemUpdate) -> ItemResponse:
    """Update an item, then invalidate both list and detail caches."""
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if req.name is not None:
        item["name"] = req.name
    if req.price is not None:
        item["price"] = req.price

    # Invalidate both list and detail caches for this item
    invalidate_cache(tags=["items:list", "items:detail"], cache=cache)

    return ItemResponse(**item)


@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int) -> None:
    """Delete an item, then invalidate the list cache."""
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")

    del _items[item_id]

    # Invalidate the cached item list
    invalidate_cache(tags=["items:list"], cache=cache)


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
