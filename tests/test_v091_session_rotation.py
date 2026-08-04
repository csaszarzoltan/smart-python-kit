"""TDD coverage for persisted refresh-token rotation and revocation."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from smartvintaawesomekit.auth.config import AuthConfig
from smartvintaawesomekit.auth.jwt import JWTManager
from smartvintaawesomekit.auth.models import SessionRecord
from smartvintaawesomekit.auth.session import SessionManager, SessionStatus
from smartvintaawesomekit.database import Base


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


def _config() -> AuthConfig:
    return AuthConfig(jwt_secret_key="x" * 48)


@pytest.mark.asyncio
async def test_rotate_refresh_token_revokes_old_and_persists_new(session: AsyncSession) -> None:
    jwt_manager = JWTManager(_config())
    manager = SessionManager(session, _config())
    original = jwt_manager.create_refresh_token("1")
    old_payload = jwt_manager.decode_token(original)
    await manager.create_session("1", old_payload["jti"])
    await session.commit()

    pair = await manager.rotate_refresh_token(original, jwt_manager)
    old = await manager.get_session(old_payload["jti"])
    new_payload = jwt_manager.decode_token(pair.refresh_token)
    new = await manager.get_session(new_payload["jti"])

    assert old is not None and old.status == SessionStatus.REVOKED.value
    assert new is not None and new.status == SessionStatus.ACTIVE.value
    assert new.user_id == 1


@pytest.mark.asyncio
async def test_rotate_rejects_reused_revoked_token(session: AsyncSession) -> None:
    jwt_manager = JWTManager(_config())
    manager = SessionManager(session, _config())
    token = jwt_manager.create_refresh_token("1")
    payload = jwt_manager.decode_token(token)
    await manager.create_session("1", payload["jti"])
    await session.commit()
    await manager.rotate_refresh_token(token, jwt_manager)

    with pytest.raises(ValueError, match="not active"):
        await manager.rotate_refresh_token(token, jwt_manager)


@pytest.mark.asyncio
async def test_rotate_rejects_missing_and_expired_sessions(session: AsyncSession) -> None:
    jwt_manager = JWTManager(_config())
    manager = SessionManager(session, _config())
    missing = jwt_manager.create_refresh_token("1")
    with pytest.raises(ValueError, match="session not found"):
        await manager.rotate_refresh_token(missing, jwt_manager)

    expired = jwt_manager.create_refresh_token("1")
    payload = jwt_manager.decode_token(expired)
    session.add(SessionRecord(user_id=1, refresh_token_jti=payload["jti"], status="active",
                              created_at=datetime.now(UTC) - timedelta(days=2),
                              expires_at=datetime.now(UTC) - timedelta(days=1)))
    await session.commit()
    with pytest.raises(ValueError, match="expired"):
        await manager.rotate_refresh_token(expired, jwt_manager)


@pytest.mark.asyncio
async def test_rotate_rejects_access_token(session: AsyncSession) -> None:
    jwt_manager = JWTManager(_config())
    manager = SessionManager(session, _config())
    with pytest.raises(ValueError, match="not a refresh token"):
        await manager.rotate_refresh_token(jwt_manager.create_access_token("1"), jwt_manager)
