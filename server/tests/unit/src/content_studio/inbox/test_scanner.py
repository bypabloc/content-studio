"""Spec 030, fase 1: el sondeo toma lo que queda estable en dos sondeos (AC-2, AC-3 y AC-6)."""

import json

from content_studio.inbox import scanner, store


def _register(conn, folder, services) -> int:
    return store.register(conn, str(folder), 'media.convert', {'target': 'mp3'}, services=services)


def _jobs(conn) -> list[dict]:
    return [dict(row) for row in conn.execute('SELECT id, kind, params FROM jobs ORDER BY id')]


def test_ac2_takes_a_file_once_it_is_stable_across_two_sweeps(conn, folder, services):
    _register(conn, folder, services)
    (folder / 'toma.wav').write_bytes(b'RIFF' * 10)

    scanner.scan_once(conn, services=services)
    assert (folder / 'toma.wav').is_file()  # el primer sondeo solo mira
    assert _jobs(conn) == []

    scanner.scan_once(conn, services=services)
    taken = folder / 'processing' / 'toma.wav'
    assert not (folder / 'toma.wav').exists()
    assert taken.is_file()
    jobs = _jobs(conn)
    assert [job['kind'] for job in jobs] == ['media.convert']
    assert json.loads(jobs[0]['params'])['input'] == str(taken.resolve())


def test_ac3_skips_partial_temporary_and_growing_files(conn, folder, services):
    _register(conn, folder, services)
    (folder / 'copiando.wav.part').write_bytes(b'x')
    (folder / 'temporal.tmp').write_bytes(b'x')
    (folder / 'crece.wav').write_bytes(b'x')

    scanner.scan_once(conn, services=services)
    (folder / 'crece.wav').write_bytes(b'x' * 100)  # sigue creciendo entre sondeos
    scanner.scan_once(conn, services=services)
    (folder / 'crece.wav').write_bytes(b'x' * 200)
    scanner.scan_once(conn, services=services)

    assert _jobs(conn) == []
    assert (folder / 'copiando.wav.part').is_file()
    assert (folder / 'temporal.tmp').is_file()
    assert (folder / 'crece.wav').is_file()


def test_ac6_job_file_with_relative_paths_is_queued_or_failed(conn, folder, services):
    _register(conn, folder, services)
    (folder / 'media').mkdir()
    (folder / 'media' / 'a.wav').write_bytes(b'RIFF')
    good = {'kind': 'media.convert', 'params': {'input': 'media/a.wav', 'target': 'mp3'}}
    (folder / 'lote.job.json').write_text(json.dumps(good), encoding='utf-8')
    bad = {'kind': 'media.convert', 'params': {'target': 'bad'}}
    (folder / 'malo.job.json').write_text(json.dumps(bad), encoding='utf-8')

    scanner.scan_once(conn, services=services)
    scanner.scan_once(conn, services=services)

    queued = [json.loads(job['params']) for job in _jobs(conn)]
    assert queued == [{'input': str((folder / 'media' / 'a.wav').resolve()), 'target': 'mp3'}]
    receipt = folder / 'failed' / 'malo.job.json'
    assert (receipt / 'malo.job.json').is_file()
    error = json.loads((receipt / 'malo.job.json.error.json').read_text(encoding='utf-8'))
    assert error['errors'][0]['code'] == 'unknown_target'
