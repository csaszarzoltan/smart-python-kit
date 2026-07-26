"""smartvintaawesomekit.testing — Testing utilities and fixtures.

Provides pytest fixtures, model factories, assertion helpers, and mock
implementations for writing fast, deterministic tests.
"""

from smartvintaawesomekit.testing.client import async_client, auth_header
from smartvintaawesomekit.testing.database import db_engine, db_session
from smartvintaawesomekit.testing.factories import (
    ModelFactory,
    RoleFactory,
    SessionRecordFactory,
    UserFactory,
    UserRoleFactory,
)
from smartvintaawesomekit.testing.helpers import (
    assert_paginated,
    assert_response,
)

__all__ = [
    "ModelFactory",
    "UserFactory",
    "RoleFactory",
    "SessionRecordFactory",
    "UserRoleFactory",
    "db_engine",
    "db_session",
    "async_client",
    "auth_header",
    "assert_response",
    "assert_paginated",
]
