"""Mock implementations for auth-domain dependencies.

Provides deterministic fakes for ``JWTManager``, ``PasswordHasher``,
``RBACManager``, and ``AuthConfig`` that return predictable values
suitable for unit tests.
"""

from __future__ import annotations

from typing import Any

from smartvintaawesomekit.auth.config import AuthConfig
from smartvintaawesomekit.auth.jwt import TokenPair


class MockAuthConfig(AuthConfig):
    """Pre-configured ``AuthConfig`` with test-safe defaults.

    All fields use fixed values so tests are deterministic and do not
    depend on environment variables.
    """

    jwt_secret_key: str = "test-secret-key-not-for-production"
    jwt_algorithm: str = "HS256"


class MockJWTManager:
    """Deterministic JWT manager for testing.

    ``create_token_pair()`` returns a ``TokenPair`` with fixed token
    strings. ``decode_token()`` returns a known payload dict.
    """

    def create_token_pair(
        self,
        subject: str = "test-subject",
        claims: dict[str, Any] | None = None,
    ) -> TokenPair:
        """Return a deterministic ``TokenPair``.

        Args:
            subject: The token subject (default: ``"test-subject"``).
            claims: Optional extra claims (ignored in mock).

        Returns:
            A TokenPair with fixed tokens.
        """
        return TokenPair(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            token_type="bearer",
            expires_in=1800,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Return a known payload for any token string.

        Args:
            token: The token string (ignored in mock).

        Returns:
            A dict with ``sub``, ``type``, and ``jti`` keys.
        """
        return {
            "sub": "test-user-id",
            "type": "access",
            "jti": "test-jti-00000000-0000-0000-0000-000000000000",
            "iat": 1700000000,
            "exp": 1700086400,
        }


class MockPasswordHasher:
    """Deterministic password hasher for testing.

    ``hash_password()`` returns a fixed string.  ``verify_password()``
    returns ``True`` when the password matches the known value
    ``"secret123"``, otherwise ``False``.
    """

    def hash_password(self, password: str) -> str:
        """Return a deterministic hash for any password.

        Args:
            password: Plaintext password (ignored in mock).

        Returns:
            A fixed hash string.
        """
        return "$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qm1Qm1Qm1Qm1Qm1Qm1Qm1Qm1Qm"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Return ``True`` for ``"secret123"``, ``False`` otherwise.

        Args:
            password: Plaintext password to verify.
            hashed: Stored hash (ignored in mock).

        Returns:
            ``True`` if password is ``"secret123"``.
        """
        return password == "secret123"


class MockRBACManager:
    """Permissive RBAC manager for testing.

    ``check_permission()`` always returns ``True``.
    ``get_user_roles()`` returns a fixed role list.
    """

    def check_permission(
        self,
        user_id: int | str | None = None,
        permission: str | None = None,
    ) -> bool:
        """Always return ``True`` — all permissions granted.

        Args:
            user_id: Ignored in mock.
            permission: Ignored in mock.

        Returns:
            Always ``True``.
        """
        return True

    def get_user_roles(self, user_id: int | str) -> list[str]:
        """Return a fixed list of roles.

        Args:
            user_id: Ignored in mock.

        Returns:
            ``["user"]``
        """
        return ["user"]
