"""Auth module configuration — environment-based settings for all auth sub-modules."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    """Auth module configuration — loaded from AUTH_* env vars."""

    jwt_secret_key: str = Field(..., description="HMAC secret for JWT signing")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="Access token TTL")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh token TTL")

    password_hash_algorithm: str = Field(
        default="bcrypt", description="Hash algorithm: bcrypt|argon2"
    )

    oauth2_google_client_id: str = Field(default="", description="Google OAuth2 client ID")
    oauth2_google_client_secret: str = Field(default="", description="Google OAuth2 client secret")
    oauth2_github_client_id: str = Field(default="", description="GitHub OAuth2 client ID")
    oauth2_github_client_secret: str = Field(default="", description="GitHub OAuth2 client secret")

    session_revocation_enabled: bool = Field(default=True, description="Enable session revocation")

    model_config = {"env_prefix": "AUTH_"}


__all__ = ["AuthConfig"]
