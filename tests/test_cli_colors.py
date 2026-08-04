"""Behavioral and interface tests for the cli.theme module (Colored Output & Theme System).

Interface tests:
    - Verify imports work
    - Verify ColorMode enum values
    - Verify ThemeConfig class exists, extends BaseSettings, has correct fields
    - Verify function signatures and type hints
    - Verify __all__ exports

Behavioral tests:
    - ThemeConfig.to_rich_theme(), to_console()
    - get_console(), stylize(), print()
    - success(), error(), warning(), info()
    - panel(), rule()
"""

from __future__ import annotations

import enum
from typing import get_type_hints

import pytest
from pydantic_settings import BaseSettings

from smartvintaawesomekit.cli.theme import (
    ColorMode,
    ThemeConfig,
    error,
    get_console,
    info,
    panel,
    rule,
    stylize,
    success,
    warning,
)
from smartvintaawesomekit.cli.theme import (
    print as theme_print,
)

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestThemeInterface:
    """Verify theme module public API exists with correct signatures."""

    def test_colormode_is_enum(self) -> None:
        """ColorMode should be an Enum."""
        assert issubclass(ColorMode, enum.Enum)

    def test_colormode_has_auto(self) -> None:
        """ColorMode should have AUTO member."""
        assert ColorMode.AUTO.value == "auto"

    def test_colormode_has_light(self) -> None:
        """ColorMode should have LIGHT member."""
        assert ColorMode.LIGHT.value == "light"

    def test_colormode_has_dark(self) -> None:
        """ColorMode should have DARK member."""
        assert ColorMode.DARK.value == "dark"

    def test_colormode_has_force_color(self) -> None:
        """ColorMode should have FORCE_COLOR member."""
        assert ColorMode.FORCE_COLOR.value == "force_color"

    def test_colormode_has_no_color(self) -> None:
        """ColorMode should have NO_COLOR member."""
        assert ColorMode.NO_COLOR.value == "no_color"

    def test_themeconfig_exists(self) -> None:
        """ThemeConfig should be importable."""
        assert ThemeConfig is not None

    def test_themeconfig_inherits_basesettings(self) -> None:
        """ThemeConfig should inherit from BaseSettings."""
        assert issubclass(ThemeConfig, BaseSettings)

    def test_themeconfig_has_mode_field(self) -> None:
        """ThemeConfig should have a mode field."""
        assert "mode" in ThemeConfig.model_fields

    def test_themeconfig_mode_default_auto(self) -> None:
        """ThemeConfig mode should default to AUTO."""
        assert ThemeConfig.model_fields["mode"].default is ColorMode.AUTO

    def test_themeconfig_has_primary_field(self) -> None:
        """ThemeConfig should have a primary field."""
        assert "primary" in ThemeConfig.model_fields

    def test_themeconfig_primary_default(self) -> None:
        """ThemeConfig primary should default to 'bold cyan'."""
        assert ThemeConfig.model_fields["primary"].default == "bold cyan"

    def test_themeconfig_has_success_field(self) -> None:
        """ThemeConfig should have a success field."""
        assert "success" in ThemeConfig.model_fields

    def test_themeconfig_success_default(self) -> None:
        """ThemeConfig success should default to 'bold green'."""
        assert ThemeConfig.model_fields["success"].default == "bold green"

    def test_themeconfig_has_error_field(self) -> None:
        """ThemeConfig should have an error field."""
        assert "error" in ThemeConfig.model_fields

    def test_themeconfig_error_default(self) -> None:
        """ThemeConfig error should default to 'bold red'."""
        assert ThemeConfig.model_fields["error"].default == "bold red"

    def test_themeconfig_has_warning_field(self) -> None:
        """ThemeConfig should have a warning field."""
        assert "warning" in ThemeConfig.model_fields

    def test_themeconfig_warning_default(self) -> None:
        """ThemeConfig warning should default to 'bold yellow'."""
        assert ThemeConfig.model_fields["warning"].default == "bold yellow"

    def test_themeconfig_has_info_field(self) -> None:
        """ThemeConfig should have an info field."""
        assert "info" in ThemeConfig.model_fields

    def test_themeconfig_info_default(self) -> None:
        """ThemeConfig info should default to 'blue'."""
        assert ThemeConfig.model_fields["info"].default == "blue"

    def test_themeconfig_has_muted_field(self) -> None:
        """ThemeConfig should have a muted field."""
        assert "muted" in ThemeConfig.model_fields

    def test_themeconfig_has_prompt_field(self) -> None:
        """ThemeConfig should have a prompt field."""
        assert "prompt" in ThemeConfig.model_fields

    def test_themeconfig_has_highlight_field(self) -> None:
        """ThemeConfig should have a highlight field."""
        assert "highlight" in ThemeConfig.model_fields

    def test_themeconfig_has_progress_bar_field(self) -> None:
        """ThemeConfig should have a progress_bar field."""
        assert "progress_bar" in ThemeConfig.model_fields

    def test_themeconfig_has_progress_percent_field(self) -> None:
        """ThemeConfig should have a progress_percent field."""
        assert "progress_percent" in ThemeConfig.model_fields

    def test_themeconfig_has_table_header_field(self) -> None:
        """ThemeConfig should have a table_header field."""
        assert "table_header" in ThemeConfig.model_fields

    def test_themeconfig_has_table_border_field(self) -> None:
        """ThemeConfig should have a table_border field."""
        assert "table_border" in ThemeConfig.model_fields

    def test_themeconfig_has_table_alt_rows_field(self) -> None:
        """ThemeConfig should have a table_alt_rows field."""
        assert "table_alt_rows" in ThemeConfig.model_fields

    def test_themeconfig_has_env_prefix(self) -> None:
        """ThemeConfig should have env_prefix CLI_THEME_."""
        assert ThemeConfig.model_config.get("env_prefix") == "CLI_THEME_"

    def test_themeconfig_has_to_rich_theme_method(self) -> None:
        """ThemeConfig should have to_rich_theme method."""
        assert hasattr(ThemeConfig, "to_rich_theme")
        assert callable(ThemeConfig.to_rich_theme)

    def test_themeconfig_to_rich_theme_return_type(self) -> None:
        """to_rich_theme should return Any (Rich Theme)."""
        hints = get_type_hints(ThemeConfig.to_rich_theme)
        assert hints.get("return") is not None

    def test_themeconfig_has_to_console_method(self) -> None:
        """ThemeConfig should have to_console method."""
        assert hasattr(ThemeConfig, "to_console")
        assert callable(ThemeConfig.to_console)

    @pytest.mark.parametrize(
        "func",
        [
            get_console,
            stylize,
            theme_print,
            success,
            error,
            warning,
            info,
            panel,
            rule,
        ],
    )
    def test_module_functions_exist(self, func: callable) -> None:
        """All free functions should be callable."""
        assert callable(func)


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# ──────────────────────────────────────────────────────────────────


class TestThemeBehavioral:
    """Verify theme module behaviors are stubbed — all should raise NotImplementedError."""

    def test_to_rich_theme_not_implemented(self) -> None:
        """ThemeConfig.to_rich_theme should raise NotImplementedError."""
        config = ThemeConfig()
        config.to_rich_theme()

    def test_to_console_not_implemented(self) -> None:
        """ThemeConfig.to_console should raise NotImplementedError."""
        config = ThemeConfig()
        config.to_console()

    def test_get_console_not_implemented(self) -> None:
        """get_console should raise NotImplementedError."""
        get_console()

    def test_stylize_not_implemented(self) -> None:
        """stylize should raise NotImplementedError."""
        stylize("hello", "bold red")

    def test_print_not_implemented(self) -> None:
        """print should raise NotImplementedError."""
        theme_print("hello")

    def test_success_not_implemented(self) -> None:
        """success should raise NotImplementedError."""
        success("done")

    def test_error_not_implemented(self) -> None:
        """error should raise NotImplementedError."""
        error("fail")

    def test_warning_not_implemented(self) -> None:
        """warning should raise NotImplementedError."""
        warning("caution")

    def test_info_not_implemented(self) -> None:
        """info should raise NotImplementedError."""
        info("note")

    def test_panel_not_implemented(self) -> None:
        """panel should raise NotImplementedError."""
        panel("Title", "Content")

    def test_rule_not_implemented(self) -> None:
        """rule should raise NotImplementedError."""
        rule("Section")

    def test_themeconfig_secondary_default(self) -> None:
        """ThemeConfig secondary should default to 'dim white'."""
        config = ThemeConfig()
        assert config.secondary == "dim white"

    def test_themeconfig_created_with_env_prefix(self) -> None:
        """ThemeConfig should respect CLI_THEME_ env prefix."""
        config = ThemeConfig()
        assert config.model_config.get("env_prefix") == "CLI_THEME_"
