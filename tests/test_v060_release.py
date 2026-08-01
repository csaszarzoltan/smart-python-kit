import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from smartvintaawesomekit.api import register_exception_handlers
from smartvintaawesomekit.cli import app

runner = CliRunner()


def test_error_contract_contains_code_fields_and_request_id():
    api = FastAPI()
    register_exception_handlers(api)

    @api.get('/missing')
    async def missing():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Widget not found')

    response = TestClient(api).get('/missing', headers={'X-Request-ID': 'req-123'})
    assert response.status_code == 404
    assert response.json() == {
        'error': {
            'code': 'not_found',
            'message': 'Widget not found',
            'fields': [],
            'request_id': 'req-123',
        }
    }


def test_validation_contract_keeps_field_paths():
    api = FastAPI()
    register_exception_handlers(api)

    @api.get('/items/{item_id}')
    async def item(item_id: int):
        return {'id': item_id}

    response = TestClient(api).get('/items/not-an-int')
    body = response.json()['error']
    assert response.status_code == 422
    assert body['code'] == 'validation_error'
    assert any(field['field'] == 'path.item_id' for field in body['fields'])


def test_inspect_reports_clean_generated_project(tmp_path: Path):
    runner.invoke(app, ['init', 'demo', '--directory', str(tmp_path)])
    result = runner.invoke(app, ['inspect', '--project', str(tmp_path / 'demo'), '--json'])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload['status'] == 'clean'
    assert payload['generator_version']
    assert payload['missing_files'] == []


def test_inspect_reports_drift_and_fails_in_check_mode(tmp_path: Path):
    runner.invoke(app, ['init', 'demo', '--directory', str(tmp_path)])
    project = tmp_path / 'demo'
    (project / 'app/main.py').write_text('# changed\n')
    result = runner.invoke(app, ['inspect', '--project', str(project), '--check', '--json'])
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload['status'] == 'drifted'
    assert 'app/main.py' in payload['modified_files']


def test_resource_generation_updates_manifest(tmp_path: Path):
    runner.invoke(app, ['init', 'demo', '--directory', str(tmp_path)])
    project = tmp_path / 'demo'
    result = runner.invoke(app, ['add-resource', 'product', '--project', str(project), '--field', 'name:str:required'])
    assert result.exit_code == 0, result.output
    manifest = json.loads((project / '.smartvinta.json').read_text())
    assert manifest['resources']['product']['fields'] == ['name:str:required']
    assert 'app/routes/products.py' in manifest['managed_files']


def test_production_doctor_rejects_placeholder_secret(tmp_path: Path):
    runner.invoke(app, ['init', 'demo', '--directory', str(tmp_path)])
    project = tmp_path / 'demo'
    (project / '.env').write_text('AUTH_JWT_SECRET_KEY=change-me\n')
    result = runner.invoke(app, ['doctor', '--project', str(project), '--environment', 'production', '--json'])
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert any(check['name'] == 'jwt-secret' and not check['ok'] for check in payload['checks'])
