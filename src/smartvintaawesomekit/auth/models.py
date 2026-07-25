"""SQLAlchemy ORM models for auth entities."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — needed at runtime by SQLAlchemy

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from smartvintaawesomekit.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "auth_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)


class UserRole(Base):
    """Many-to-many User-Role association."""

    __tablename__ = "auth_user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("auth_roles.id"), primary_key=True)


class SessionRecord(Base):
    """Refresh token session tracking."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"), index=True)
    refresh_token_jti: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    expires_at: Mapped[datetime] = mapped_column()


__all__ = ["User", "Role", "UserRole", "SessionRecord"]
