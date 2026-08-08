"""Smart configuration module — pydantic-settings wrappers with sensible defaults.

Provides validated, environment-aware configuration for micro-SaaS applications.
Supports nested sub-configs for database, API, and CORS with env-var loading.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database connection configuration sub-model."""

    url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Database connection URL",
    )
    echo: bool = Field(default=False, description="SQLAlchemy echo mode")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")

    model_config = {"env_prefix": "DB_"}


class APIConfig(BaseSettings):
    """API server configuration sub-model."""

    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, description="Bind port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    title: str = Field(default="Smart API", description="API title")

    model_config = {"env_prefix": "API_"}


class CORSConfig(BaseSettings):
    """CORS configuration sub-model."""

    origins: list[str] = Field(default=["*"], description="Allowed origins")
    methods: list[str] = Field(
        default=["*"],
        description="Allowed HTTP methods",
    )
    headers: list[str] = Field(
        default=["*"],
        description="Allowed HTTP headers",
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials")

    model_config = {"env_prefix": "CORS_"}


class SecurityConfig(BaseSettings):
    """Security middleware configuration sub-model.

    Maps to the security module's SecurityConfig dataclass. Provides
    environment-variable loading for rate limiting and CORS settings.
    """

    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")
    enable_cors_hardening: bool = Field(default=True, description="Enable CORS hardening")
    enable_security_headers: bool = Field(default=True, description="Enable security headers")
    enable_request_size_limit: bool = Field(default=True, description="Enable request size limits")
    enable_input_sanitization: bool = Field(
        default=True, description="Enable input sanitization",
    )
    reject_wildcard_in_production: bool = Field(
        default=True, description="Reject wildcard CORS in production",
    )

    model_config = {"env_prefix": "SECURITY_"}


class SmartConfig(BaseSettings):
    """Top-level configuration with sensible defaults for micro-SaaS patterns.

    Combines database, API, CORS, security, and application-level settings.
    Loads from environment variables and .env files with type validation.
    """

    app_name: str = Field(default="smart-app", description="Application name")
    environment: str = Field(default="development", description="Runtime environment")
    log_level: str = Field(default="INFO", description="Logging level")
    secret_key: str = Field(default="", description="Secret key for encryption")
    debug: bool = Field(default=False, description="Global debug flag")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    feature_flags: dict[str, bool] = Field(
        default_factory=lambda: {
            "enable_telemetry": False,
            "enable_rate_limiting": True,
            "enable_caching": False,
        },
        description="Feature flags",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def is_production(self) -> bool:
        """Check if running in production environment.

        Returns:
            True if the environment field equals 'production' (case-insensitive).
        """
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment.

        Returns:
            True if the environment field equals 'development' (case-insensitive).
        """
        return self.environment.lower() == "development"

    def get_database_url(self) -> str:
        """Get the resolved database URL.

        Returns:
            The database connection URL from the database sub-config.
        """
        return self.database.url

    def get_feature_flag(self, name: str) -> bool:
        """Get a feature flag value by name.

        Args:
            name: The feature flag name to look up.

        Returns:
            The flag value, or False if the flag is not defined.
        """
        return self.feature_flags.get(name, False)


__all__ = [
    "SmartConfig",
    "DatabaseConfig",
    "APIConfig",
    "CORSConfig",
    "SecurityConfig",
]
