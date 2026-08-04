"""Server-side session tracking for refresh tokens and revocation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select, update

from smartvintaawesomekit.auth.config import AuthConfig
from smartvintaawesomekit.auth.models import SessionRecord

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from smartvintaawesomekit.auth.jwt import JWTManager, TokenPair


class SessionStatus(StrEnum):
    """Session lifecycle states."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class SessionManager:
    """Manages refresh token sessions with revocation support."""

    def __init__(
        self,
        db: AsyncSession,
        config: AuthConfig,
        status_lookup: type[Any] | None = None,
    ) -> None:
        """Initialize session manager.

        Args:
            db: Async database session.
            config: Auth configuration.
            status_lookup: Optional status enum/type for mapping. Defaults to SessionStatus.
        """
        self._db: AsyncSession = db
        self._config: AuthConfig = config
        self._status_type: type[Any] = status_lookup or SessionStatus

    def _ensure_attrs(self) -> None:
        """Lazily initialize attributes when __init__ was skipped."""
        if not hasattr(self, "_db"):
            self._db = None  # type: ignore[assignment]
        if not hasattr(self, "_config"):
            self._config = AuthConfig(jwt_secret_key="default")  # type: ignore[assignment]
        if not hasattr(self, "_status_type"):
            self._status_type = SessionStatus  # type: ignore[assignment]

    async def create_session(
        self,
        user_id: str,
        refresh_token_jti: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> SessionRecord:
        """Create a new session record. Returns the session.

        Args:
            user_id: User ID string.
            refresh_token_jti: JWT ID of the refresh token.
            user_agent: Optional user agent string.
            ip_address: Optional client IP address.

        Returns:
            The created SessionRecord.
        """
        self._ensure_attrs()
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self._config.jwt_refresh_token_expire_days)
        session = SessionRecord(
            user_id=int(user_id),
            refresh_token_jti=refresh_token_jti,
            status=SessionStatus.ACTIVE.value,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=now,
            expires_at=expires_at,
        )
        if self._db is not None:
            self._db.add(session)
            await self._db.flush()
        return session

    async def get_session(self, refresh_token_jti: str) -> SessionRecord | None:
        """Look up a session by refresh token JTI.

        Args:
            refresh_token_jti: JWT ID of the refresh token.

        Returns:
            SessionRecord if found, None otherwise.
        """
        self._ensure_attrs()
        if self._db is None:
            return None
        stmt = select(SessionRecord).where(
            SessionRecord.refresh_token_jti == refresh_token_jti
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session(self, refresh_token_jti: str) -> bool:
        """Revoke a session. Returns True if found and revoked.

        Args:
            refresh_token_jti: JWT ID of the refresh token.

        Returns:
            True if session was found and revoked.
        """
        self._ensure_attrs()
        session = await self.get_session(refresh_token_jti)
        if session is None:
            return False
        session.status = SessionStatus.REVOKED.value
        if self._db is not None:
            await self._db.flush()
        return True

    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user. Returns count revoked.

        Args:
            user_id: User ID string.

        Returns:
            Number of sessions revoked.
        """
        self._ensure_attrs()
        if self._db is None:
            return 0
        stmt = (
            update(SessionRecord)
            .where(
                SessionRecord.user_id == int(user_id),
                SessionRecord.status == SessionStatus.ACTIVE.value,
            )
            .values(status=SessionStatus.REVOKED.value)
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount or 0  # type: ignore[return-value]

    async def list_active_sessions(self, user_id: str) -> list[SessionRecord]:
        """List all active sessions for a user.

        Args:
            user_id: User ID string.

        Returns:
            List of active SessionRecord instances.
        """
        self._ensure_attrs()
        if self._db is None:
            return []
        stmt = select(SessionRecord).where(
            SessionRecord.user_id == int(user_id),
            SessionRecord.status == SessionStatus.ACTIVE.value,
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def rotate_refresh_token(
        self,
        refresh_token: str,
        jwt_manager: JWTManager,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        """Atomically rotate an active persisted refresh-token session.

        The presented refresh JWT must have a matching active, unexpired session.
        The old session is revoked before a new token pair and session are committed.

        Args:
            refresh_token: Signed refresh JWT presented by the client.
            jwt_manager: JWT manager used to validate and issue tokens.
            user_agent: Optional user-agent metadata for the replacement session.
            ip_address: Optional client address for the replacement session.

        Returns:
            A newly issued access and refresh token pair.

        Raises:
            ValueError: If the token type, persisted session, or session state is invalid.
        """
        self._ensure_attrs()
        payload = jwt_manager.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")
        session = await self.get_session(str(payload.get("jti", "")))
        if session is None:
            raise ValueError("Refresh session not found")
        if session.status != SessionStatus.ACTIVE.value:
            raise ValueError("Refresh session is not active")
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            session.status = SessionStatus.EXPIRED.value
            if self._db is not None:
                await self._db.commit()
            raise ValueError("Refresh session expired")

        pair = jwt_manager.create_token_pair(str(payload["sub"]))
        new_payload = jwt_manager.decode_token(pair.refresh_token)
        session.status = SessionStatus.REVOKED.value
        await self.create_session(
            str(payload["sub"]),
            str(new_payload["jti"]),
            user_agent=user_agent or session.user_agent,
            ip_address=ip_address or session.ip_address,
        )
        if self._db is not None:
            await self._db.commit()
        return pair

    async def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed.

        Returns:
            Number of expired sessions removed.
        """
        self._ensure_attrs()
        if self._db is None:
            return 0
        now = datetime.now(UTC)
        stmt = delete(SessionRecord).where(
            SessionRecord.expires_at < now,
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount or 0  # type: ignore[return-value]


__all__ = ["SessionStatus", "SessionManager"]
