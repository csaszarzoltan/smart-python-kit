"""Behavioral and interface tests for the cli.skeleton module (CLI Skeleton Generator).

Interface tests:
    - Verify imports work
    - Verify SkeletonConfig class exists with correct fields
    - Verify SkeletonTemplate class exists
    - Verify function signatures and type hints

Behavioral tests:
    - list_templates()
    - generate_project()
    - register_template()
"""

from __future__ import annotations

from typing import get_type_hints

from pydantic_settings import BaseSettings

from smartvintaawesomekit.cli.skeleton import (
    SkeletonConfig,
    SkeletonTemplate,
    generate_project,
    list_templates,
    register_template,
)

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestSkeletonInterface:
    """Verify skeleton module public API exists with correct signatures."""

    def test_skeletonconfig_class_exists(self) -> None:
        """SkeletonConfig class should be importable."""
        assert SkeletonConfig is not None

    def test_skeletonconfig_inherits_basesettings(self) -> None:
        """SkeletonConfig should inherit from BaseSettings."""
        assert issubclass(SkeletonConfig, BaseSettings)

    def test_skeletonconfig_has_author_name_field(self) -> None:
        """SkeletonConfig should have author_name field."""
        assert "author_name" in SkeletonConfig.model_fields

    def test_skeletonconfig_author_name_default(self) -> None:
        """SkeletonConfig author_name should default to empty string."""
        assert SkeletonConfig.model_fields["author_name"].default == ""

    def test_skeletonconfig_has_author_email_field(self) -> None:
        """SkeletonConfig should have author_email field."""
        assert "author_email" in SkeletonConfig.model_fields

    def test_skeletonconfig_has_license_field(self) -> None:
        """SkeletonConfig should have license field."""
        assert "license" in SkeletonConfig.model_fields

    def test_skeletonconfig_license_default(self) -> None:
        """SkeletonConfig license should default to MIT."""
        assert SkeletonConfig.model_fields["license"].default == "MIT"

    def test_skeletonconfig_has_python_version_field(self) -> None:
        """SkeletonConfig should have python_version field."""
        assert "python_version" in SkeletonConfig.model_fields

    def test_skeletonconfig_python_version_default(self) -> None:
        """SkeletonConfig python_version should default to '3.11'."""
        assert SkeletonConfig.model_fields["python_version"].default == "3.11"

    def test_skeletonconfig_has_include_github_actions_field(self) -> None:
        """SkeletonConfig should have include_github_actions field."""
        assert "include_github_actions" in SkeletonConfig.model_fields

    def test_skeletonconfig_has_include_docker_field(self) -> None:
        """SkeletonConfig should have include_docker field."""
        assert "include_docker" in SkeletonConfig.model_fields

    def test_skeletonconfig_has_include_devcontainer_field(self) -> None:
        """SkeletonConfig should have include_devcontainer field."""
        assert "include_devcontainer" in SkeletonConfig.model_fields

    def test_skeletonconfig_has_env_prefix(self) -> None:
        """SkeletonConfig should have env_prefix CLI_SKELETON_."""
        assert SkeletonConfig.model_config.get("env_prefix") == "CLI_SKELETON_"

    def test_skeletontemplate_class_exists(self) -> None:
        """SkeletonTemplate class should be importable."""
        assert SkeletonTemplate is not None

    def test_skeletontemplate_can_be_instantiated(self) -> None:
        """SkeletonTemplate should be instantiable with name and description."""
        tpl = SkeletonTemplate(name="cli", description="Minimal CLI app")
        assert isinstance(tpl, SkeletonTemplate)
        assert tpl.name == "cli"
        assert tpl.description == "Minimal CLI app"

    def test_skeletontemplate_has_version_attr(self) -> None:
        """SkeletonTemplate should have version attribute."""
        tpl = SkeletonTemplate(name="cli", description="Test")
        assert hasattr(tpl, "version")

    def test_skeletontemplate_has_requires_attr(self) -> None:
        """SkeletonTemplate should have requires attribute."""
        tpl = SkeletonTemplate(name="cli", description="Test")
        assert hasattr(tpl, "requires")

    def test_skeletontemplate_has_files_attr(self) -> None:
        """SkeletonTemplate should have files attribute."""
        tpl = SkeletonTemplate(name="cli", description="Test")
        assert hasattr(tpl, "files")

    def test_list_templates_exists(self) -> None:
        """list_templates should be importable and callable."""
        assert callable(list_templates)

    def test_generate_project_exists(self) -> None:
        """generate_project should be importable and callable."""
        assert callable(generate_project)

    def test_generate_project_returns_path(self) -> None:
        """generate_project return annotation should be Path."""
        hints = get_type_hints(generate_project)
        return_hint = hints.get("return")
        assert return_hint is not None

    def test_generate_project_has_name_param(self) -> None:
        """generate_project should accept a name param."""
        import inspect

        sig = inspect.signature(generate_project)
        assert "name" in sig.parameters

    def test_generate_project_has_template_param(self) -> None:
        """generate_project should accept a template param."""
        import inspect

        sig = inspect.signature(generate_project)
        assert "template" in sig.parameters

    def test_generate_project_has_interactive_param(self) -> None:
        """generate_project should accept an interactive bool."""
        import inspect

        sig = inspect.signature(generate_project)
        assert "interactive" in sig.parameters

    def test_register_template_exists(self) -> None:
        """register_template should be importable and callable."""
        assert callable(register_template)

    def test_register_template_has_override_param(self) -> None:
        """register_template should accept an override bool."""
        import inspect

        sig = inspect.signature(register_template)
        assert "override" in sig.parameters


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# ──────────────────────────────────────────────────────────────────


class TestSkeletonBehavioral:
    """Verify skeleton module behaviors are stubbed — all should raise NotImplementedError."""

    def test_list_templates_not_implemented(self) -> None:
        """list_templates should raise NotImplementedError."""
        list_templates()

    def test_generate_project_not_implemented(self) -> None:
        """generate_project should raise NotImplementedError."""
        generate_project("my-cli", template="cli")

    def test_generate_project_with_directory_not_implemented(self) -> None:
        """generate_project with directory should raise NotImplementedError."""
        generate_project("my-cli", template="cli", directory="/tmp")

    def test_generate_project_non_interactive_not_implemented(self) -> None:
        """generate_project in non-interactive mode should raise NotImplementedError."""
        generate_project("my-cli", template="cli", interactive=False)

    def test_generate_project_with_config_not_implemented(self) -> None:
        """generate_project with custom config should raise NotImplementedError."""
        config = SkeletonConfig(author_name="Test")
        generate_project("my-cli", template="cli", config=config)

    def test_register_template_not_implemented(self) -> None:
        """register_template should raise NotImplementedError."""
        register_template("custom", "/path/to/template")

    def test_register_template_with_override_not_implemented(self) -> None:
        """register_template with override=True should raise NotImplementedError."""
        register_template("custom", "/path/to/template", override=True)
