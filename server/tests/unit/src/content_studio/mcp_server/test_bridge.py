"""Spec 029, fase 1: el puente con una API falsa (AC-4, AC-5, AC-7 y AC-8), sin server."""

import asyncio
from typing import Any

from content_studio import gpu_lock
from content_studio.mcp_server.api_client import ApiFailure
from content_studio.mcp_server.bridge import Bridge


class FakeApi:
    """Responde las rutas que el puente usa; cada GET de un trabajo avanza la lista de estados."""

    def __init__(self, jobs: list[dict[str, Any]] | None = None, post: Any = None) -> None:
        self._jobs = list(jobs or [])
        self._post = post
        self.posted: list[tuple[str, Any]] = []

    def get(self, path: str) -> Any:
        if path.endswith('/outputs') or path == '/jobs':
            return []
        return self._jobs[0] if len(self._jobs) == 1 else self._jobs.pop(0)

    def post(self, path: str, body: Any = None) -> Any:
        self.posted.append((path, body))
        if isinstance(self._post, Exception):
            raise self._post
        if self._post is not None:
            return self._post
        return {'id': 1, 'kind': 'narration', 'status': 'queued', 'progress': 0, 'resource': 'gpu'}


def _bridge(tmp_path, api: FakeApi) -> Bridge:
    return Bridge(tmp_path / 'content-studio.db', api=lambda: api, poll_s=0.01, main=tmp_path)


def _job(status: str, progress: float = 0.0, **extra: Any) -> dict[str, Any]:
    return {'id': 1, 'kind': 'music', 'status': status, 'progress': progress, 'resource': 'gpu', 'stage': None, **extra}


def test_ac4_missing_input_path_is_error_and_not_queued(tmp_path):
    api = FakeApi()
    missing = tmp_path / 'x.wav'
    result = asyncio.run(_bridge(tmp_path, api).call('studio_transcribe', {'input_path': str(missing)}))
    assert result.is_error
    assert result.structured['error']['code'] == 'input_not_found'
    assert str(missing) in result.text
    assert api.posted == []


def test_ac8_invalid_params_return_service_errors(tmp_path):
    body = {'errors': [{'code': 'unknown_engine', 'params': {'model': 'nope'}}]}
    api = FakeApi(post=ApiFailure(422, body))
    result = asyncio.run(_bridge(tmp_path, api).call('studio_submit_job', {'kind': 'narration', 'params': {}}))
    assert result.is_error
    assert result.structured['error']['code'] == 'validation_failed'
    assert [item['code'] for item in result.structured['errors']] == ['unknown_engine']
    assert result.structured['errors'][0]['params'] == {'model': 'nope'}


def test_ac5_wait_reports_progress_and_times_out_without_error(tmp_path):
    api = FakeApi(jobs=[_job('running', 0.2, stage='mezcla'), _job('running', 0.6), _job('done', 1.0)])
    seen: list[tuple[float, float | None, str | None]] = []

    async def notify(progress: float, total: float | None, message: str | None) -> None:
        seen.append((progress, total, message))

    result = asyncio.run(_bridge(tmp_path, api).call('studio_wait_job', {'job_id': 1, 'timeout_s': 5}, notify))
    assert result.structured['status'] == 'done'
    assert [item[0] for item in seen] == [0.2, 0.6, 1.0]
    assert seen[0][2] == 'mezcla'

    slow = FakeApi(jobs=[_job('running', 0.1)])
    expired = asyncio.run(_bridge(tmp_path, slow).call('studio_wait_job', {'job_id': 1, 'timeout_s': 0}))
    assert not expired.is_error
    assert expired.structured['timed_out'] is True
    assert expired.structured['status'] == 'running'


def test_ac7_gpu_queued_says_who_holds_it(tmp_path):
    assert gpu_lock.take(tmp_path, 'otra-sesion', ['studio']) is None  # otra sesión toma la GPU (formato real)
    api = FakeApi(jobs=[_job('queued')])
    result = asyncio.run(_bridge(tmp_path, api).call('studio_get_job', {'job_id': 1}))
    job = result.structured['job']
    assert job['status'] == 'waiting_gpu'
    assert job['waiting_on'].endswith('otra-sesion')


def test_cancel_calls_the_job_cancel_endpoint(tmp_path):
    api = FakeApi(jobs=[_job('cancelled')])
    result = asyncio.run(_bridge(tmp_path, api).call('studio_cancel_job', {'job_id': 1}))
    assert api.posted[0][0] == '/jobs/1/cancel'
    assert result.structured['status'] == 'cancelled'


def test_job_id_must_be_integer(tmp_path):
    result = asyncio.run(_bridge(tmp_path, FakeApi()).call('studio_get_job', {'job_id': 'uno'}))
    assert result.is_error
    assert result.structured['error']['code'] == 'job_id_required'
