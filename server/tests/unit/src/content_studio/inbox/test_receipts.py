"""Spec 030, fase 1: los recibos de los trabajos terminados (AC-4 y AC-5)."""

import json

from content_studio.db import jobs
from content_studio.inbox import scanner, store


def _taken(conn, folder, services, status: str, **fields) -> int:
    """Una carpeta con un archivo ya tomado (en processing/) cuyo trabajo quedó en `status`."""
    folder_id = store.register(conn, str(folder), 'media.convert', {'target': 'mp3'}, services=services)
    (folder / 'processing').mkdir(exist_ok=True)
    (folder / 'processing' / 'a.wav').write_bytes(b'RIFF')
    job_id = jobs.insert(conn, 'media.convert', 'cpu', {'input': 'a.wav'})
    jobs.update(conn, job_id, status=status, **fields)
    store.add_item(conn, folder_id, 'a.wav', size=4, mtime=1.0, state='processing', job_id=job_id)
    return job_id


def test_ac4_done_keeps_the_original_outputs_and_a_result_receipt(conn, folder, services, tmp_path):
    output = tmp_path / 'out' / 'media' / 'la-salida'
    output.mkdir(parents=True)
    (output / 'a.mp3').write_bytes(b'ID3')
    (output / 'params.json').write_text('{}', encoding='utf-8')
    job_id = _taken(conn, folder, services, 'done', output_dir=str(output))

    scanner.scan_once(conn, services=services)

    done = folder / 'done' / 'a.wav'
    assert (done / 'a.wav').is_file()
    assert (done / 'a.mp3').read_bytes() == b'ID3'
    assert not (done / 'params.json').exists()
    assert not (folder / 'processing' / 'a.wav').exists()
    receipt = json.loads((done / 'a.wav.result.json').read_text(encoding='utf-8'))
    assert receipt['job_id'] == job_id
    assert receipt['outputs'] == [str((done / 'a.mp3').resolve())]


def test_ac5_failed_keeps_the_original_and_an_error_receipt(conn, folder, services):
    job_id = _taken(conn, folder, services, 'error', error_code='process_failed', error_detail='ffmpeg salió con 1')

    scanner.scan_once(conn, services=services)

    failed = folder / 'failed' / 'a.wav'
    assert (failed / 'a.wav').is_file()
    error = json.loads((failed / 'a.wav.error.json').read_text(encoding='utf-8'))
    assert error['job_id'] == job_id
    assert error['code'] == 'process_failed'
    assert error['message'] == 'ffmpeg salió con 1'


def test_cancelled_goes_to_failed_with_its_own_code(conn, folder, services):
    job_id = _taken(conn, folder, services, 'cancelled')

    scanner.scan_once(conn, services=services)

    error = json.loads((folder / 'failed' / 'a.wav' / 'a.wav.error.json').read_text(encoding='utf-8'))
    assert error == {'job_id': job_id, 'code': 'cancelled', 'message': 'cancelled', 'errors': []}
