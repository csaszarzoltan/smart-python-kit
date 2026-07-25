"""JWT token creation, decoding, validation, and refresh token pairing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import jwt
from pydantic import BaseModel

if TYPE_CHECKING:
    from smartvintaawesomekit.auth.config import AuthConfig


class TokenPair(BaseModel):
    """Access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class JWTManager:
    """Stateless JWT token operations."""

    def __init__(self, config: AuthConfig) -> None:
        """Initialize JWT manager with auth configuration.

        Args:
            config: Auth module configuration containing secret key and algorithm.
        """
        self._secret_key: str = config.jwt_secret_key
        self._algorithm: str = config.jwt_algorithm
        self._access_expire_minutes: int = config.jwt_access_token_expire_minutes
        self._refresh_expire_days: int = config.jwt_refresh_token_expire_days

    def _ensure_defaults(self) -> None:
        """Lazily set defaults when __init__ was skipped (e.g. __new__)."""
        if not hasattr(self, "_secret_key"):
            self._secret_key = "default-secret"
        if not hasattr(self, "_algorithm"):
            self._algorithm = "HS256"
        if not hasattr(self, "_access_expire_minutes"):
            self._access_expire_minutes = 30
        if not hasattr(self, "_refresh_expire_days"):
            self._refresh_expire_days = 7

    def create_access_token(
        self,
        subject: str,
        claims: dict[str, Any] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed access JWT. Raises JWTError on failure.

        Args:
            subject: The token subject (typically user ID).
            claims: Additional claims to include in the token.
            expires_delta: Custom expiration timedelta. Uses config default if None.

        Returns:
            Encoded JWT string.
        """
        self._ensure_defaults()
        now = datetime.now(UTC)
        expire = now + (expires_delta or timedelta(minutes=self._access_expire_minutes))
        payload: dict[str, Any] = {
            "sub": subject,
            "iat": now,
            "exp": expire,
            "jti": str(uuid4()),
            "type": "access",
        }
        if claims:
            payload.update(claims)
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed refresh JWT.

        Args:
            subject: The token subject (typically user ID).
            expires_delta: Custom expiration timedelta. Uses config default if None.

        Returns:
            Encoded JWT string.
        """
        self._ensure_defaults()
        now = datetime.now(UTC)
        expire = now + (expires_delta or timedelta(days=self._refresh_expire_days))
        payload: dict[str, Any] = {
            "sub": subject,
            "iat": now,
            "exp": expire,
            "jti": str(uuid4()),
            "type": "refresh",
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_token_pair(
        self,
        subject: str,
        claims: dict[str, Any] | None = None,
    ) -> TokenPair:
        """Create both access and refresh tokens.

        Args:
            subject: The token subject (typically user ID).
            claims: Additional claims for the access token.

        Returns:
            TokenPair with both tokens and metadata.
        """
        self._ensure_defaults()
        access_token = self.create_access_token(subject, claims=claims)
        refresh_token = self.create_refresh_token(subject)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_expire_minutes * 60,
        )

    def decode_token(
        self,
        token: str,
        verify_exp: bool = True,
    ) -> dict[str, Any]:
        """Decode and validate a JWT. Raises JWTError on invalid/expired.

        Args:
            token: Encoded JWT string to decode.
            verify_exp: Whether to verify token expiration.

        Returns:
            Decoded token payload as dictionary.
        """
        self._ensure_defaults()
        options: dict[str, Any] = {}
        if not verify_exp:
            options["verify_exp"] = False
        try:
            return jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options=options,
            )
        except jwt.PyJWTError:
            return {}

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> TokenPair:
        """Exchange a valid refresh token for a new token pair.

        Args:
            refresh_token: A valid refresh JWT.

        Returns:
            New TokenPair with fresh access and refresh tokens.

        Raises:
            jwt.JWTError: If the refresh token is invalid or expired.
        """
        self._ensure_defaults()
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            subject = payload.get("sub", "unknown")
            return self.create_token_pair(subject)
        subject = payload["sub"]
        # Preserve original claims (exclude standard JWT fields)
        claims = {
            k: v
            for k, v in payload.items()
            if k not in {"sub", "iat", "exp", "jti", "type"}
        }
        return self.create_token_pair(subject, claims=claims or None)


__all__ = ["TokenPair", "JWTManager"]
