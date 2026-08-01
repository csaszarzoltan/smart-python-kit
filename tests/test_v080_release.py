import json
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit.cli import app

runner = CliRunner()


def make_project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    return tmp_path / "demo"


def test_generated_project_has_ci_and_quality_script(tmp_path: Path):
    project = make_project(tmp_path)
    assert (project / ".github/workflows/quality.yml").is_file()
    assert (project / "scripts/check.py").is_file()
    workflow = (project / ".github/workflows/quality.yml").read_text()
    assert "scripts/check.py" in workflow
    assert "pytest" in (project / "scripts/check.py").read_text()


def test_upgrade_plan_reports_current_project(tmp_path: Path):
    project = make_project(tmp_path)
    result = runner.invoke(app, ["upgrade-plan", "--project", str(project), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "current"
    assert payload["project_version"] == payload["available_version"]
    assert payload["safe_actions"] == []


def test_upgrade_plan_classifies_old_clean_project_as_safe(tmp_path: Path):
    project = make_project(tmp_path)
    manifest_path = project / ".smartvinta.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["generator_version"] = "0.7.0"
    manifest_path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["upgrade-plan", "--project", str(project), "--json"])
    payload = json.loads(result.stdout)
    assert payload["status"] == "upgrade_available"
    assert "regenerate-managed-files" in payload["safe_actions"]
    assert payload["conflicts"] == []


def test_upgrade_plan_reports_modified_files_as_conflicts(tmp_path: Path):
    project = make_project(tmp_path)
    manifest_path = project / ".smartvinta.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["generator_version"] = "0.7.0"
    manifest_path.write_text(json.dumps(manifest))
    (project / "app/main.py").write_text("# locally changed\n")
    result = runner.invoke(app, ["upgrade-plan", "--project", str(project), "--check", "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["status"] == "conflicts"
    assert "app/main.py" in payload["conflicts"]


def test_manifest_repair_is_previewable_and_restores_missing_metadata(tmp_path: Path):
    project = make_project(tmp_path)
    manifest_path = project / ".smartvinta.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.pop("schema_version")
    manifest_path.write_text(json.dumps(manifest))
    preview = runner.invoke(app, ["manifest-repair", "--project", str(project), "--dry-run", "--json"])
    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["changes"] == ["set schema_version to 1"]
    applied = runner.invoke(app, ["manifest-repair", "--project", str(project), "--json"])
    assert applied.exit_code == 0
    assert json.loads(manifest_path.read_text())["schema_version"] == 1
    assert (project / ".smartvinta.json.bak").is_file()


def test_manifest_repair_refuses_unknown_newer_schema(tmp_path: Path):
    project = make_project(tmp_path)
    manifest_path = project / ".smartvinta.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_version"] = 999
    manifest_path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["manifest-repair", "--project", str(project), "--json"])
    assert result.exit_code != 0
