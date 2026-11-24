"""Servicio de proxies del editor (spec 018, D-3)."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.services import editor_proxy


def test_proxy_runs_as_a_cpu_job():
    """Los proxies usan FFmpeg por CPU y no toman el turno de GPU."""
    assert editor_proxy.RESOURCE == 'cpu'


def test_validate_requires_an_existing_project_and_video(tmp_path: Path):
    """La cola rechaza el proyecto o la fuente ausentes antes de iniciar FFmpeg."""
    project = tmp_path / 'project.json'
    source = tmp_path / 'clip.mp4'
    project.write_text('{}', encoding='utf-8')

    assert editor_proxy.validate({'project': str(project), 'source': str(source)}) == [
        {'code': 'fs_media_not_found', 'params': {'path': str(source)}}
    ]
    assert editor_proxy.validate({'source': str(source)})[0]['code'] == 'editor_project_not_found'


def test_validate_rejects_non_video_sources(tmp_path: Path):
    """Solo los archivos de video admitidos se pueden convertir a proxy."""
    project = tmp_path / 'project.json'
    source = tmp_path / 'track.wav'
    project.touch()
    source.touch()

    assert editor_proxy.validate({'project': str(project), 'source': str(source)}) == [
        {'code': 'unreadable_media', 'params': {}}
    ]


def test_validate_resolves_relative_source_from_the_project_folder(tmp_path: Path):
    """Los clips del documento usan rutas relativas a la carpeta del proyecto."""
    folder = tmp_path / 'project'
    project = folder / 'project.json'
    source = folder / 'media' / 'clip.mp4'
    source.parent.mkdir(parents=True)
    project.write_text('{}', encoding='utf-8')
    source.touch()

    assert editor_proxy.validate({'project': str(project), 'source': 'media/clip.mp4'}) == []


def test_build_command_runs_proxy_module_with_project_and_source(tmp_path: Path):
    """El worker pasa las dos rutas al módulo del proxy."""
    project = tmp_path / 'project.json'
    source = tmp_path / 'clip.mp4'

    assert editor_proxy.build_command({'project': str(project), 'source': str(source)}, tmp_path) == [
        sys.executable,
        '-m',
        'content_studio.editor.proxy',
        '--project',
        str(project),
        '--source',
        str(source),
    ]
