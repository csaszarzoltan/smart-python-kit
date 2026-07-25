"""OAuth2 authorization code flow for Google and GitHub providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode

import httpx

from smartvintaawesomekit.auth.config import AuthConfig  # noqa: TC001 — used at runtime


class OAuth2Provider(ABC):
    """Abstract base for OAuth2 providers."""

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Return the OAuth2 authorization URL with state parameter."""
        ...

    @abstractmethod
    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens. Returns token data."""
        ...

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user profile from provider API."""
        ...


class GoogleOAuth2(OAuth2Provider):
    """Google OAuth2 provider."""

    _AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    _TOKEN_URL = "https://oauth2.googleapis.com/token"
    _USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    _DEFAULT_SCOPES = "openid email profile"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        """Initialize Google OAuth2 provider.

        Args:
            client_id: Google OAuth2 client ID.
            client_secret: Google OAuth2 client secret.
            redirect_uri: OAuth2 redirect URI.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Return the Google OAuth2 authorization URL with state parameter.

        Args:
            state: CSRF protection state parameter.

        Returns:
            Full authorization URL string.
        """
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": self._DEFAULT_SCOPES,
            "state": state,
            "access_type": "offline",
        }
        return f"{self._AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from Google callback.

        Returns:
            Token data dictionary.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user profile from Google API.

        Args:
            access_token: OAuth2 access token.

        Returns:
            User profile dictionary.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()


class GitHubOAuth2(OAuth2Provider):
    """GitHub OAuth2 provider."""

    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    _TOKEN_URL = "https://github.com/login/oauth/access_token"
    _USERINFO_URL = "https://api.github.com/user"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        """Initialize GitHub OAuth2 provider.

        Args:
            client_id: GitHub OAuth2 client ID.
            client_secret: GitHub OAuth2 client secret.
            redirect_uri: OAuth2 redirect URI.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Return the GitHub OAuth2 authorization URL with state parameter.

        Args:
            state: CSRF protection state parameter.

        Returns:
            Full authorization URL string.
        """
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return f"{self._AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from GitHub callback.

        Returns:
            Token data dictionary.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._TOKEN_URL,
                json={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user profile from GitHub API.

        Args:
            access_token: OAuth2 access token.

        Returns:
            User profile dictionary.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()


_PROVIDER_MAP: dict[str, type[OAuth2Provider]] = {
    "google": GoogleOAuth2,
    "github": GitHubOAuth2,
}


def get_provider(name: str, config: AuthConfig, redirect_uri: str) -> OAuth2Provider:
    """Factory: get provider by name (google | github). Raises ValueError if unknown/disabled.

    Args:
        name: Provider name ('google' or 'github').
        config: Auth configuration with client credentials.
        redirect_uri: OAuth2 redirect URI.

    Returns:
        Configured OAuth2Provider instance.

    Raises:
        ValueError: If provider name is unknown or credentials are not configured.
    """
    name_lower = name.lower()
    if name_lower not in _PROVIDER_MAP:
        raise ValueError(
            f"Unknown OAuth2 provider '{name}'. Available: {list(_PROVIDER_MAP.keys())}"
        )

    if name_lower == "google":
        client_id = config.oauth2_google_client_id or ""
        client_secret = config.oauth2_google_client_secret or ""
        return GoogleOAuth2(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

    client_id = config.oauth2_github_client_id or ""
    client_secret = config.oauth2_github_client_secret or ""
    return GitHubOAuth2(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )


__all__ = ["OAuth2Provider", "GoogleOAuth2", "GitHubOAuth2", "get_provider"]
