"""TDD acceptance coverage for safe managed-file upgrade application."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit import __version__
from smartvintaawesomekit.cli import app

runner = CliRunner()


def _legacy_project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "minimal"])
    assert result.exit_code == 0, result.output
    project = tmp_path / "demo"
    manifest_path = project / ".smartvinta.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["generator_version"] = "0.8.0"
    readme = project / "README.md"
    legacy = readme.read_text().replace(f"SmartVintaAwesomeKit {__version__}", "SmartVintaAwesomeKit 0.8.0")
    readme.write_text(legacy)
    encoded = __import__("base64").b64encode(legacy.encode()).decode("ascii")
    manifest["managed_files"]["README.md"] = {
        "sha256": hashlib.sha256(legacy.encode()).hexdigest(),
        "baseline": encoded,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return project


def test_upgrade_apply_dry_run_is_read_only_and_lists_changes(tmp_path: Path) -> None:
    project = _legacy_project(tmp_path)
    before = (project / "README.md").read_bytes()
    result = runner.invoke(app, ["upgrade-apply", "--project", str(project), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert "README.md" in payload["updated_files"]
    assert (project / "README.md").read_bytes() == before
    assert not (project / ".smartvinta.json.upgrade.bak").exists()


def test_upgrade_apply_updates_only_clean_managed_files_and_manifest(tmp_path: Path) -> None:
    project = _legacy_project(tmp_path)
    result = runner.invoke(app, ["upgrade-apply", "--project", str(project), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    manifest = json.loads((project / ".smartvinta.json").read_text())
    assert payload["status"] == "applied"
    assert manifest["generator_version"] == __version__
    assert (project / ".smartvinta.json.upgrade.bak").is_file()
    readme = (project / "README.md").read_bytes()
    assert manifest["managed_files"]["README.md"]["sha256"] == hashlib.sha256(readme).hexdigest()


def test_upgrade_apply_blocks_conflicts_without_partial_writes(tmp_path: Path) -> None:
    project = _legacy_project(tmp_path)
    readme = project / "README.md"
    readme.write_text(readme.read_text() + "\nlocal owner change\n")
    manifest_before = (project / ".smartvinta.json").read_bytes()
    result = runner.invoke(app, ["upgrade-apply", "--project", str(project), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "conflicts"
    assert "README.md" in payload["conflicts"]
    assert (project / ".smartvinta.json").read_bytes() == manifest_before
    assert not (project / ".smartvinta.json.upgrade.bak").exists()


def test_upgrade_apply_rejects_unknown_manifest_schema(tmp_path: Path) -> None:
    project = _legacy_project(tmp_path)
    path = project / ".smartvinta.json"
    manifest = json.loads(path.read_text())
    manifest["schema_version"] = 99
    path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["upgrade-apply", "--project", str(project), "--json"])
    assert result.exit_code != 0
