"""Mock implementations for dependencies used across the test suite.

Provides test doubles for auth, cache, HTTP, and database layers so
tests remain deterministic and fast.
"""

from smartvintaawesomekit.testing.mocks.auth import (
    MockAuthConfig,
    MockJWTManager,
    MockPasswordHasher,
    MockRBACManager,
)
from smartvintaawesomekit.testing.mocks.cache import (
    MockCacheBackend,
    MockCacheInvalidation,
)
from smartvintaawesomekit.testing.mocks.database import (
    MockAsyncSession,
    MockCRUD,
)
from smartvintaawesomekit.testing.mocks.http import (
    MockAsyncClient,
    MockResponse,
)

__all__ = [
    "MockAuthConfig",
    "MockJWTManager",
    "MockPasswordHasher",
    "MockRBACManager",
    "MockCacheBackend",
    "MockCacheInvalidation",
    "MockAsyncClient",
    "MockResponse",
    "MockAsyncSession",
    "MockCRUD",
]
