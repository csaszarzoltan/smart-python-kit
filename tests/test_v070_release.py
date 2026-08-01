import json
from pathlib import Path

from typer.testing import CliRunner

from smartvintaawesomekit.cli import app

runner = CliRunner()


def _project(tmp_path: Path) -> Path:
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path)])
    assert result.exit_code == 0, result.output
    return tmp_path / "demo"


def test_manifest_has_versioned_schema_and_baselines(tmp_path: Path):
    project = _project(tmp_path)
    manifest = json.loads((project / ".smartvinta.json").read_text())
    assert manifest["schema_version"] == 1
    assert manifest["managed_files"]["app/main.py"]["sha256"]
    assert manifest["managed_files"]["app/main.py"]["baseline"]


def test_inspect_diff_explains_modified_file(tmp_path: Path):
    project = _project(tmp_path)
    main = project / "app/main.py"
    main.write_text(main.read_text() + "\n# intentional change\n")
    result = runner.invoke(app, ["inspect", "--project", str(project), "--diff", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "drifted"
    assert "# intentional change" in payload["diffs"]["app/main.py"]


def test_manifest_accept_is_previewable_and_updates_selected_hash(tmp_path: Path):
    project = _project(tmp_path)
    main = project / "app/main.py"
    main.write_text(main.read_text() + "\n# accepted\n")
    preview = runner.invoke(app, ["manifest-accept", "app/main.py", "--project", str(project), "--dry-run", "--json"])
    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["dry_run"] is True
    drift = runner.invoke(app, ["inspect", "--project", str(project), "--check", "--json"])
    assert drift.exit_code == 1
    accepted = runner.invoke(app, ["manifest-accept", "app/main.py", "--project", str(project), "--json"])
    assert accepted.exit_code == 0, accepted.output
    clean = runner.invoke(app, ["inspect", "--project", str(project), "--check", "--json"])
    assert clean.exit_code == 0, clean.output


def test_manifest_accept_refuses_unmanaged_and_sensitive_files(tmp_path: Path):
    project = _project(tmp_path)
    (project / ".env").write_text("SECRET=value\n")
    unmanaged = runner.invoke(app, ["manifest-accept", "notes.txt", "--project", str(project)])
    sensitive = runner.invoke(app, ["manifest-accept", ".env", "--project", str(project)])
    assert unmanaged.exit_code != 0
    assert sensitive.exit_code != 0


def test_doctor_reports_optional_capabilities_without_secrets(tmp_path: Path):
    project = _project(tmp_path)
    result = runner.invoke(app, ["doctor", "--project", str(project), "--json"])
    payload = json.loads(result.stdout)
    names = {check["name"] for check in payload["checks"]}
    assert {"optional-redis", "optional-alembic"} <= names
    assert "redis://" not in result.stdout
