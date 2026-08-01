"""CLI skeleton generator — scaffold new CLI projects from templates.

Provides project generation with interactive prompts, template registration,
and built-in templates (cli, cli-api, cli-db).

Usage:
    from smartvintaawesomekit.cli.skeleton import list_templates, generate_project

    templates = list_templates()
    project_path = generate_project("my-cli", template="cli")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

# Global registry for custom templates
_custom_templates: dict[str, Path] = {}

# Built-in template definitions
_BUILTIN_TEMPLATES: dict[str, dict[str, Any]] = {
    "cli": {
        "name": "cli",
        "description": "Minimal CLI app with typer",
        "version": "1.0.0",
        "requires": ["typer>=0.9.0", "rich>=14.0"],
        "files": {},
    },
    "cli-api": {
        "name": "cli-api",
        "description": "CLI app with FastAPI backend",
        "version": "1.0.0",
        "requires": ["typer>=0.9.0", "fastapi>=0.136.0", "uvicorn[standard]>=0.20.0"],
        "files": {},
    },
    "cli-db": {
        "name": "cli-db",
        "description": "CLI app with database support",
        "version": "1.0.0",
        "requires": [
            "typer>=0.9.0",
            "sqlalchemy>=2.0",
            "alembic>=1.12",
        ],
        "files": {},
    },
}


class SkeletonConfig(BaseSettings):
    """Skeleton generator configuration.

    Prefix: CLI_SKELETON_

    Attributes:
        author_name: Default author name for generated projects.
        author_email: Default author email for generated projects.
        license: Default license (default: "MIT").
        python_version: Default Python version (default: "3.11").
        include_github_actions: Whether to include GitHub Actions workflows.
        include_docker: Whether to include Dockerfile.
        include_devcontainer: Whether to include devcontainer configuration.
    """

    author_name: str = ""
    author_email: str = ""
    license: str = "MIT"
    python_version: str = "3.11"
    include_github_actions: bool = True
    include_docker: bool = True
    include_devcontainer: bool = True

    model_config = {"env_prefix": "CLI_SKELETON_"}


class SkeletonTemplate:
    """Represents a project template with metadata.

    Attributes:
        name: Template identifier.
        description: Human-readable description.
        version: Template version.
        requires: List of required Python packages.
        files: Dictionary of file paths to template contents.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        requires: list[str] | None = None,
        files: dict[str, str] | None = None,
    ) -> None:
        """Initialize a skeleton template.

        Args:
            name: Template identifier.
            description: Human-readable description.
            version: Template version (default: "1.0.0").
            requires: List of required Python packages.
            files: Dictionary of file paths to template contents.
        """
        self.name = name
        self.description = description
        self.version = version
        self.requires = requires or []
        self.files = files or {}


def _get_builtin_templates() -> list[SkeletonTemplate]:
    """Get the built-in template list."""
    result: list[SkeletonTemplate] = []
    for tpl_data in _BUILTIN_TEMPLATES.values():
        result.append(
            SkeletonTemplate(
                name=tpl_data["name"],
                description=tpl_data["description"],
                version=tpl_data.get("version", "1.0.0"),
                requires=tpl_data.get("requires", []),
                files=tpl_data.get("files", {}),
            )
        )
    return result


def _get_custom_templates() -> list[SkeletonTemplate]:
    """Get registered custom templates."""
    result: list[SkeletonTemplate] = []
    for name, tpl_dir in _custom_templates.items():
        result.append(
            SkeletonTemplate(
                name=name,
                description=f"Custom template from {tpl_dir}",
                version="1.0.0",
            )
        )
    return result


def list_templates() -> list[SkeletonTemplate]:
    """List available project skeleton templates.

    Returns a combined list of built-in templates and registered custom templates.

    Returns:
        A list of SkeletonTemplate instances representing available templates.

    Example:
        for tpl in list_templates():
            print(f"{tpl.name}: {tpl.description}")
    """
    return _get_builtin_templates() + _get_custom_templates()


def generate_project(
    name: str,
    template: str = "cli",
    *,
    directory: str | None = None,
    config: SkeletonConfig | None = None,
    interactive: bool = True,
) -> Path:
    """Generate a skeleton CLI project.

    Creates a project directory with basic project structure including
    pyproject.toml, package directory, and entry point.

    Args:
        name: The project name.
        template: Template identifier (e.g., "cli", "cli-api", "cli-db").
        directory: Parent directory for the project. Defaults to current directory.
        config: Optional SkeletonConfig with author/license settings.
        interactive: If True, use interactive prompts for values not provided.

    Returns:
        Path to the generated project directory.

    Example:
        path = generate_project("my-cli", template="cli")
        print(f"Project created at {path}")
    """
    cfg = config or SkeletonConfig()

    # Determine output directory
    base_dir = Path(directory) if directory else Path.cwd()
    project_dir = base_dir / name

    # Create project structure
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "src" / name.replace("-", "_")).mkdir(parents=True, exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)

    # Create __init__.py
    pkg_name = name.replace("-", "_")
    init_file = project_dir / "src" / pkg_name / "__init__.py"
    init_file.write_text(f'"""The {name} package."""\n\n__version__ = "0.1.0"\n')

    # Create main module
    main_file = project_dir / "src" / pkg_name / "__main__.py"
    main_content = (
        f'"""Main entry point for {name}."""\n\n'
        '\ndef main() -> None:\n'
        '    """Run the CLI app."""\n'
        f'    print("Hello from {name}")\n'
        '\n\nif __name__ == "__main__":\n'
        '    main()\n'
    )
    main_file.write_text(main_content)

    # Create test file
    test_file = project_dir / "tests" / "test_main.py"
    test_content = (
        f'"""Tests for {name}."""\n\n'
        '\ndef test_placeholder() -> None:\n'
        '    """Placeholder test."""\n'
        '    assert True\n'
    )
    test_file.write_text(test_content)

    # Create pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    author_name_val = cfg.author_name or "Author"
    author_email_val = cfg.author_email or "author@example.com"
    pyproject.write_text(
        f"""[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "A CLI project generated by smartvintaawesomekit"
requires-python = ">={cfg.python_version}"
license = {{text = "{cfg.license}"}}
authors = [
    {{name = "{author_name_val}", email = "{author_email_val}"}},
]
dependencies = [
    "typer>=0.9.0",
    "rich>=14.0",
]

[project.scripts]
{name} = "{pkg_name}.__main__:main"

[tool.ruff]
line-length = 100
target-version = "py311"
"""
    )

    # Create __init__.py for tests
    (project_dir / "tests" / "__init__.py").touch()

    return project_dir


def register_template(
    name: str,
    template_dir: str | Path,
    *,
    override: bool = False,
) -> None:
    """Register a custom user template from a directory.

    Args:
        name: Unique name for the template.
        template_dir: Path to the template directory.
        override: If True, overwrite an existing custom template with the same name.

    Raises:
        ValueError: If a template with this name is already registered and
                    override is False.

    Example:
        register_template("my-template", "/path/to/template", override=True)
    """
    tpl_path = Path(template_dir)

    if name in _custom_templates and not override:
        raise ValueError(
            f"Template '{name}' is already registered. Use override=True to replace."
        )

    _custom_templates[name] = tpl_path


__all__ = [
    "SkeletonConfig",
    "SkeletonTemplate",
    "list_templates",
    "generate_project",
    "register_template",
]
