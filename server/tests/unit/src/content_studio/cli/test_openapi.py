"""`studio openapi` (spec 005, D-3): imprime el schema de la API sin levantar el server ni tocar la base."""

from __future__ import annotations

import json

from content_studio.cli.main import main


def test_openapi_prints_the_schema_of_the_api(capsys):
    assert main(['openapi']) == 0

    schema = json.loads(capsys.readouterr().out)

    assert {'/jobs', '/jobs/{job_id}', '/queue', '/events', '/settings/{key}'} <= set(schema['paths'])
    assert {'Job', 'QueueState', 'SettingOut'} <= set(schema['components']['schemas'])


def test_openapi_job_schema_lists_the_fields_the_client_shows(capsys):
    main(['openapi'])

    job = json.loads(capsys.readouterr().out)['components']['schemas']['Job']

    assert {'id', 'kind', 'status', 'progress', 'stage', 'error_code', 'params'} <= set(job['properties'])
