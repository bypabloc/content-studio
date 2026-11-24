"""Servicio `subtitles.translate` (spec 014, D-8): resuelve el proyecto y arma el comando de whisper en inglés."""

from __future__ import annotations

from pathlib import Path

from content_studio.db import connection, schema, subtitle_projects
from content_studio.services import subtitles_translate
from content_studio.subtitles.document import save
from content_studio.subtitles.sources import from_cleaner

WORDS = [{'word': 'hola', 'start': 0.2, 'end': 0.9}]


def _project(tmp_path: Path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    doc = tmp_path / 'proyecto' / 'subtitles.json'
    save(from_cleaner(WORDS, source_path='clase.mp4', language='es'), doc)
    return conn, subtitle_projects.insert(conn, 'clase', 'clase.mp4', str(doc))


def test_the_service_is_gpu_because_whisper_loads_a_model():
    """Traducir carga whisper: recurso gpu, con el candado compartido."""
    assert subtitles_translate.RESOURCE == 'gpu'


def test_a_missing_project_is_refused(tmp_path):
    """Un proyecto que no existe da `subtitle_project_not_found`."""
    conn, _ = _project(tmp_path)
    params, _ = subtitles_translate.prepare(conn, {'project_id': 999})

    assert subtitles_translate.validate(params) == [
        {'code': 'subtitle_project_not_found', 'params': {'project_id': 999}}
    ]


def test_an_unknown_model_is_refused(tmp_path):
    """Un modelo que no está en el catálogo de whisper da `unknown_engine`."""
    conn, project_id = _project(tmp_path)
    params, _ = subtitles_translate.prepare(conn, {'project_id': project_id, 'model': 'no-existe'})

    assert subtitles_translate.validate(params) == [{'code': 'unknown_engine', 'params': {'model': 'no-existe'}}]


def test_build_command_asks_whisper_to_translate_the_source_into_the_job_folder(tmp_path):
    """El comando es el de `transcribe_main` con `--task translate`, sobre el video del proyecto."""
    conn, project_id = _project(tmp_path)
    params, _ = subtitles_translate.prepare(conn, {'project_id': project_id, 'model': 'small'})

    command = subtitles_translate.build_command(params, Path('/salida'))

    assert command[command.index('--task') + 1] == 'translate'
    assert command[command.index('--input') + 1] == 'clase.mp4'
    assert command[command.index('--model') + 1] == 'small'
    assert command[command.index('--out') + 1] == str(Path('/salida') / 'words.json')
