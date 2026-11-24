"""Runner de un trabajo (spec 004, D-4): parsea `@@progress` del proceso y deja el resto en logs/jobs/<id>.log."""

from __future__ import annotations

import sys

import pytest

from content_studio.db import connection, jobs, schema
from content_studio.jobs import runner


@pytest.fixture
def conn(tmp_path):
    db = connection.connect(tmp_path / 'base.db')
    schema.migrate(db)
    yield db
    db.close()


def _python(code: str) -> list[str]:
    return [sys.executable, '-c', code]


def test_progress_lines_update_the_job_and_the_rest_goes_to_the_log(conn, tmp_path):
    job_id = jobs.insert(conn, 'music', 'gpu', {})
    code = 'print("Seed: 7"); print("@@progress {\\"p\\": 0.5, \\"stage\\": \\"x\\"}"); print("fin")'

    code_returned = runner.run(conn, job_id, _python(code), log_dir=tmp_path / 'logs')

    job = jobs.get(conn, job_id)
    assert code_returned == 0
    assert (job['progress'], job['stage']) == (0.5, 'x')
    log = (tmp_path / 'logs' / f'{job_id}.log').read_text(encoding='utf-8')
    assert 'Seed: 7' in log and 'fin' in log
    assert '@@progress' not in log


def test_the_exit_code_of_the_process_is_returned(conn, tmp_path):
    job_id = jobs.insert(conn, 'music', 'gpu', {})

    assert runner.run(conn, job_id, _python('raise SystemExit(3)'), log_dir=tmp_path) == 3
