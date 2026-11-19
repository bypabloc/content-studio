"""Modelos de respuesta de la API (spec 005, D-3): los valores que el schema promete son los que la base permite."""

from __future__ import annotations

from content_studio.api.schemas import Job, QueueState, SettingOut


def test_job_status_and_resource_are_the_ones_the_database_allows():
    properties = Job.model_json_schema()['properties']

    assert properties['status']['enum'] == ['queued', 'running', 'done', 'error', 'cancelled']
    assert properties['resource']['enum'] == ['gpu', 'cpu']


def test_queue_and_setting_schemas_name_their_fields():
    assert set(QueueState.model_json_schema()['properties']) == {'paused'}
    assert set(SettingOut.model_json_schema()['properties']) == {'key', 'value'}
