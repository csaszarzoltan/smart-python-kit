import json
from pathlib import Path
from typer.testing import CliRunner
from smartvintaawesomekit.cli import app
runner = CliRunner()

def test_dry_run_is_non_destructive(tmp_path: Path):
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--dry-run", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert not (tmp_path / "demo").exists()
    assert "app/main.py" in payload["files"]

def test_api_preset_generates_guided_structure(tmp_path: Path):
    result = runner.invoke(app, ["init", "demo-app", "--directory", str(tmp_path), "--preset", "api"])
    assert result.exit_code == 0, result.output
    project = tmp_path / "demo-app"
    for path in [".env.example", ".smartvinta.json", "app/routes/items.py", "tests/test_items.py"]:
        assert (project / path).is_file()
    assert "Next steps" in result.stdout and "/docs" in result.stdout

def test_existing_destination_is_not_overwritten(tmp_path: Path):
    project = tmp_path / "demo"; project.mkdir(); marker = project / "keep.txt"; marker.write_text("keep")
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path)])
    assert result.exit_code != 0 and marker.read_text() == "keep"

def test_invalid_name_fails_before_writing(tmp_path: Path):
    result = runner.invoke(app, ["init", "../bad", "--directory", str(tmp_path)])
    assert result.exit_code != 0

def test_postgresql_selection_changes_output(tmp_path: Path):
    result = runner.invoke(app, ["init", "demo", "--directory", str(tmp_path), "--database", "postgresql"])
    assert result.exit_code == 0
    assert "asyncpg" in (tmp_path / "demo/pyproject.toml").read_text()
    assert "postgresql+asyncpg" in (tmp_path / "demo/.env.example").read_text()

def test_doctor_reports_json_status(tmp_path: Path):
    runner.invoke(app, ["init", "demo", "--directory", str(tmp_path)])
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path / "demo"), "--json"])
    assert result.exit_code == 0 and json.loads(result.stdout)["ok"] is True
