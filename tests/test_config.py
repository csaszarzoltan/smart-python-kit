"""Behavioral and interface tests for the config module.

Interface tests:
    - Verify imports work
    - Verify classes exist
    - Verify class/method signatures and type hints
    - Verify default values

Behavioral tests:
    - Environment detection methods
    - Database URL resolution
    - Feature flag access
"""

from __future__ import annotations

from typing import get_type_hints

from smartvintaawesomekit.config import (
    APIConfig,
    CORSConfig,
    DatabaseConfig,
    SmartConfig,
)

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────

class TestConfigInterface:
    """Verify config module public API exists with correct signatures."""

    def test_smartconfig_class_exists(self) -> None:
        """SmartConfig class should be importable."""
        assert SmartConfig is not None

    def test_databaseconfig_class_exists(self) -> None:
        """DatabaseConfig class should be importable."""
        assert DatabaseConfig is not None

    def test_apiconfig_class_exists(self) -> None:
        """APIConfig class should be importable."""
        assert APIConfig is not None

    def test_corsconfig_class_exists(self) -> None:
        """CORSConfig class should be importable."""
        assert CORSConfig is not None

    def test_smartconfig_inherits_basesettings(self) -> None:
        """SmartConfig should inherit from BaseSettings."""
        from pydantic_settings import BaseSettings
        assert issubclass(SmartConfig, BaseSettings)

    def test_databaseconfig_inherits_basesettings(self) -> None:
        """DatabaseConfig should inherit from BaseSettings."""
        from pydantic_settings import BaseSettings
        assert issubclass(DatabaseConfig, BaseSettings)

    def test_apiconfig_inherits_basesettings(self) -> None:
        """APIConfig should inherit from BaseSettings."""
        from pydantic_settings import BaseSettings
        assert issubclass(APIConfig, BaseSettings)

    def test_corsconfig_inherits_basesettings(self) -> None:
        """CORSConfig should inherit from BaseSettings."""
        from pydantic_settings import BaseSettings
        assert issubclass(CORSConfig, BaseSettings)

    def test_smartconfig_has_app_name_field(self) -> None:
        """SmartConfig should have an app_name field."""
        assert "app_name" in SmartConfig.model_fields

    def test_smartconfig_has_environment_field(self) -> None:
        """SmartConfig should have an environment field."""
        assert "environment" in SmartConfig.model_fields

    def test_smartconfig_has_log_level_field(self) -> None:
        """SmartConfig should have a log_level field."""
        assert "log_level" in SmartConfig.model_fields

    def test_smartconfig_has_secret_key_field(self) -> None:
        """SmartConfig should have a secret_key field."""
        assert "secret_key" in SmartConfig.model_fields

    def test_smartconfig_has_debug_field(self) -> None:
        """SmartConfig should have a debug field."""
        assert "debug" in SmartConfig.model_fields

    def test_smartconfig_has_database_sub_config(self) -> None:
        """SmartConfig should have a database sub-config field."""
        assert "database" in SmartConfig.model_fields

    def test_smartconfig_has_api_sub_config(self) -> None:
        """SmartConfig should have an api sub-config field."""
        assert "api" in SmartConfig.model_fields

    def test_smartconfig_has_cors_sub_config(self) -> None:
        """SmartConfig should have a cors sub-config field."""
        assert "cors" in SmartConfig.model_fields

    def test_smartconfig_has_feature_flags_field(self) -> None:
        """SmartConfig should have a feature_flags field."""
        assert "feature_flags" in SmartConfig.model_fields

    def test_smartconfig_has_is_production_method(self) -> None:
        """SmartConfig should have is_production method."""
        assert hasattr(SmartConfig, "is_production")
        assert callable(SmartConfig.is_production)

    def test_smartconfig_has_is_development_method(self) -> None:
        """SmartConfig should have is_development method."""
        assert hasattr(SmartConfig, "is_development")
        assert callable(SmartConfig.is_development)

    def test_smartconfig_has_get_database_url_method(self) -> None:
        """SmartConfig should have get_database_url method."""
        assert hasattr(SmartConfig, "get_database_url")
        assert callable(SmartConfig.get_database_url)

    def test_smartconfig_has_get_feature_flag_method(self) -> None:
        """SmartConfig should have get_feature_flag method."""
        assert hasattr(SmartConfig, "get_feature_flag")
        assert callable(SmartConfig.get_feature_flag)

    def test_databaseconfig_has_url_field(self) -> None:
        """DatabaseConfig should have a url field."""
        assert "url" in DatabaseConfig.model_fields

    def test_databaseconfig_has_echo_field(self) -> None:
        """DatabaseConfig should have an echo field."""
        assert "echo" in DatabaseConfig.model_fields

    def test_databaseconfig_has_pool_size_field(self) -> None:
        """DatabaseConfig should have a pool_size field."""
        assert "pool_size" in DatabaseConfig.model_fields

    def test_databaseconfig_has_max_overflow_field(self) -> None:
        """DatabaseConfig should have a max_overflow field."""
        assert "max_overflow" in DatabaseConfig.model_fields

    def test_apiconfig_has_host_field(self) -> None:
        """APIConfig should have a host field."""
        assert "host" in APIConfig.model_fields

    def test_apiconfig_has_port_field(self) -> None:
        """APIConfig should have a port field."""
        assert "port" in APIConfig.model_fields

    def test_apiconfig_has_debug_field(self) -> None:
        """APIConfig should have a debug field."""
        assert "debug" in APIConfig.model_fields

    def test_corsconfig_has_origins_field(self) -> None:
        """CORSConfig should have an origins field."""
        assert "origins" in CORSConfig.model_fields

    def test_corsconfig_has_allow_credentials_field(self) -> None:
        """CORSConfig should have an allow_credentials field."""
        assert "allow_credentials" in CORSConfig.model_fields

    def test_smartconfig_return_type_is_production(self) -> None:
        """is_production should return bool."""
        hints = get_type_hints(SmartConfig.is_production)
        assert hints.get("return") is bool

    def test_smartconfig_return_type_is_development(self) -> None:
        """is_development should return bool."""
        hints = get_type_hints(SmartConfig.is_development)
        assert hints.get("return") is bool

    def test_smartconfig_return_type_get_database_url(self) -> None:
        """get_database_url should return str."""
        hints = get_type_hints(SmartConfig.get_database_url)
        assert hints.get("return") is str

    def test_smartconfig_return_type_get_feature_flag(self) -> None:
        """get_feature_flag should return bool."""
        hints = get_type_hints(SmartConfig.get_feature_flag)
        assert hints.get("return") is bool

    def test_all_exports_listed(self) -> None:
        """Verify __all__ exports match expected public API."""
        from smartvintaawesomekit import config
        exports = config.__all__
        assert "SmartConfig" in exports
        assert "DatabaseConfig" in exports
        assert "APIConfig" in exports
        assert "CORSConfig" in exports
        assert "SecurityConfig" in exports


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates as test FAILURE.
# ──────────────────────────────────────────────────────────────────

class TestConfigBehavioral:
    """Verify config module behaviors are stubbed — all should raise NotImplementedError."""

    def test_is_production_not_implemented(self) -> None:
        """SmartConfig.is_production should raise NotImplementedError."""
        config = SmartConfig()
        config.is_production()  # raises NotImplementedError → test FAILS

    def test_is_development_not_implemented(self) -> None:
        """SmartConfig.is_development should raise NotImplementedError."""
        config = SmartConfig()
        config.is_development()  # raises NotImplementedError → test FAILS

    def test_get_database_url_not_implemented(self) -> None:
        """SmartConfig.get_database_url should raise NotImplementedError."""
        config = SmartConfig()
        config.get_database_url()  # raises NotImplementedError → test FAILS

    def test_get_feature_flag_not_implemented(self) -> None:
        """SmartConfig.get_feature_flag should raise NotImplementedError."""
        config = SmartConfig()
        config.get_feature_flag("enable_caching")  # raises NotImplementedError → test FAILS
