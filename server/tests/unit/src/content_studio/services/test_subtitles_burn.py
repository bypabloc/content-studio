"""Servicio `subtitles.burn` (spec 014, D-7): resuelve el documento del proyecto, valida el preset y arma el comando."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_studio.db import connection, schema, subtitle_projects
from content_studio.services import subtitles_burn
from content_studio.subtitles.document import save
from content_studio.subtitles.sources import from_cleaner
from content_studio.system import tools

WORDS = [{'word': 'hola', 'start': 0.2, 'end': 0.9}]


@pytest.fixture(autouse=True)
def libass_present(monkeypatch):
    """El ffmpeg del equipo de la prueba trae libass; el caso sin libass lo cambia dentro de su prueba."""
    monkeypatch.setattr(tools, 'detect', lambda: {'ffmpeg': None, 'git': None, 'gpu': None, 'subtitles_filter': True})


def _project(tmp_path: Path, source: str = 'clip.mp4'):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    doc = tmp_path / 'proyecto' / 'subtitles.json'
    save(from_cleaner(WORDS, source_path=source, language='es'), doc)
    return conn, subtitle_projects.insert(conn, 'clip', source, str(doc)), doc


def test_prepare_adds_the_document_of_the_project(tmp_path):
    """El documento sale del registro del proyecto: el comando no necesita la base."""
    conn, project_id, doc = _project(tmp_path)

    params, group = subtitles_burn.prepare(conn, {'project_id': project_id, 'preset': 'reels'})

    assert params['doc'] == str(doc)
    assert group is None


def test_a_video_project_with_a_known_preset_is_valid(tmp_path):
    """Un proyecto de video con un preset conocido no tiene errores."""
    conn, project_id, _ = _project(tmp_path)
    params, _ = subtitles_burn.prepare(conn, {'project_id': project_id, 'preset': 'reels'})

    assert subtitles_burn.validate(params) == []


def test_a_missing_project_is_refused(tmp_path):
    """Un proyecto que no existe da el error del catálogo con su id."""
    conn, _, _ = _project(tmp_path)
    params, _ = subtitles_burn.prepare(conn, {'project_id': 999})

    assert subtitles_burn.validate(params) == [{'code': 'subtitle_project_not_found', 'params': {'project_id': 999}}]


def test_an_unknown_preset_is_refused(tmp_path):
    """Un preset que no existe da `unknown_style`."""
    conn, project_id, _ = _project(tmp_path)
    params, _ = subtitles_burn.prepare(conn, {'project_id': project_id, 'preset': 'inexistente'})

    assert subtitles_burn.validate(params) == [{'code': 'unknown_style', 'params': {'style': 'inexistente'}}]


def test_an_audio_only_project_is_not_burned(tmp_path):
    """Con solo audio no hay video que quemar: se exporta, no se quema (spec 014, D-7)."""
    conn, project_id, _ = _project(tmp_path, source='voz.wav')
    params, _ = subtitles_burn.prepare(conn, {'project_id': project_id})

    assert subtitles_burn.validate(params) == [{'code': 'burn_needs_video', 'params': {}}]


def test_without_libass_the_burn_is_refused_before_queueing(tmp_path, monkeypatch):
    """Sin libass en el ffmpeg del sistema, quemar se rechaza con `ffmpeg_no_libass` antes de encolar (014, D-7)."""
    conn, project_id, _ = _project(tmp_path)
    monkeypatch.setattr(tools, 'detect', lambda: {'ffmpeg': None, 'git': None, 'gpu': None, 'subtitles_filter': False})
    params, _ = subtitles_burn.prepare(conn, {'project_id': project_id})

    assert subtitles_burn.validate(params) == [{'code': 'ffmpeg_no_libass', 'params': {}}]


def test_build_command_runs_burn_main_on_the_document(tmp_path):
    """El comando es `burn_main` con el documento, el preset y la carpeta del trabajo."""
    command = subtitles_burn.build_command({'doc': '/x/subtitles.json', 'preset': 'reels'}, Path('/salida'))

    assert command[1:3] == ['-m', 'content_studio.subtitles.burn_main']
    assert command[command.index('--doc') + 1] == '/x/subtitles.json'
    assert command[command.index('--preset') + 1] == 'reels'


def test_the_service_is_cpu_and_maps_exit_code_3_to_no_libass():
    """Quemar es ffmpeg, no modelo: recurso cpu. El código 3 del proceso es `ffmpeg_no_libass`."""
    assert subtitles_burn.RESOURCE == 'cpu'
    assert subtitles_burn.ERROR_CODES == {3: 'ffmpeg_no_libass'}
