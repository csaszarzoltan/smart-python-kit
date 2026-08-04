"""Behavioral and interface tests for the cli module.

Interface tests:
    - Verify imports work
    - Verify Typer app exists
    - Verify commands registered
    - Verify function signatures

Behavioral tests:
    - init command raises NotImplementedError
"""

from __future__ import annotations

from smartvintaawesomekit.cli import app

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────

class TestCliInterface:
    """Verify cli module public API exists with correct signatures."""

    def test_app_exists(self) -> None:
        """Typer app should be importable."""
        assert app is not None

    def test_app_is_typer(self) -> None:
        """app should be a Typer instance."""
        import typer
        assert isinstance(app, typer.Typer)

    def test_app_has_init_command(self) -> None:
        """app should have init command registered."""
        names = {c.callback.__name__ for c in app.registered_commands if c.callback}
        assert "init" in names

    def test_app_has_version_command(self) -> None:
        """app should have version command registered."""
        names = {c.callback.__name__ for c in app.registered_commands if c.callback}
        assert "version" in names

    def test_app_has_callback(self) -> None:
        """app should have a callback registered."""
        assert app.registered_callback is not None

    def test_app_name_is_correct(self) -> None:
        """app name should be smartvintaawesomekit."""
        assert app.info.name == "smartvintaawesomekit"

    def test_all_exports_listed(self) -> None:
        """Verify __all__ exports match expected public API."""
        from smartvintaawesomekit import cli
        exports = cli.__all__
        assert "app" in exports


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates as test FAILURE.
# ──────────────────────────────────────────────────────────────────

class TestCliBehavioral:
    """Verify implemented CLI behavior."""

    def test_init_generates_project(self, tmp_path) -> None:
        """Invoking init should generate a runnable project structure."""
        cmd = next(c for c in app.registered_commands
                   if c.callback and c.callback.__name__ == "init")
        cmd.callback(project_name="test-project", directory=str(tmp_path))
        assert (tmp_path / "test-project" / "app" / "main.py").is_file()
