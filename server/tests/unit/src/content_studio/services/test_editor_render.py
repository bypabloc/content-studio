"""Servicio `editor.render` (spec 017, D-4): trabajo de ffmpeg en la cola, sin candado de la GPU."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.services import editor_render


def test_the_service_runs_on_the_cpu_not_the_gpu_lock():
    """Es ffmpeg: no carga modelos, así que no toma el candado de la GPU."""
    assert editor_render.RESOURCE == 'cpu'


def test_validate_accepts_a_project_and_a_known_format():
    """Con un `project.json` y un formato de audio conocido no hay errores."""
    assert editor_render.validate({'doc': 'out/editor/x/project.json', 'format': 'wav'}) == []


def test_validate_rejects_a_missing_project_and_an_unknown_format():
    """Sin proyecto, `editor_project_not_found`; con un formato que no existe, `unknown_target`."""
    assert editor_render.validate({'format': 'wav'})[0]['code'] == 'editor_project_not_found'
    assert editor_render.validate({'doc': 'x/project.json', 'format': 'exe'}) == [
        {'code': 'unknown_target', 'params': {'target': 'exe'}}
    ]


def test_validate_rejects_an_unknown_loudness_preset():
    """Un preset de sonoridad que no existe, `unknown_preset`."""
    errors = editor_render.validate({'doc': 'x/project.json', 'format': 'wav', 'normalize': 'radio'})

    assert errors == [{'code': 'unknown_preset', 'params': {'preset': 'radio'}}]


def test_validate_rejects_an_incomplete_or_reversed_marker_range():
    """Un tramo debe tener inicio y fin válidos antes de encolarse."""
    assert editor_render.validate({'doc': 'x/project.json', 'format': 'wav', 'start': 3, 'end': 2}) == [
        {'code': 'bad_render_range', 'params': {'start': 3, 'end': 2}}
    ]
    assert editor_render.validate({'doc': 'x/project.json', 'format': 'wav', 'start': 2}) == [
        {'code': 'bad_render_range', 'params': {'start': 2, 'end': None}}
    ]


def test_build_command_runs_the_render_main_with_the_project_format_and_folder(tmp_path: Path):
    """El comando es `render_main` con el `project.json`, el formato, la sonoridad (si la hay) y la carpeta."""
    command = editor_render.build_command({'doc': 'x/project.json', 'format': 'wav', 'normalize': 'podcast'}, tmp_path)

    assert command == [
        sys.executable,
        '-m',
        'content_studio.editor.render_main',
        '--project',
        'x/project.json',
        '--format',
        'wav',
        '--normalize',
        'podcast',
        '--out-dir',
        str(tmp_path),
    ]


def test_build_command_passes_marker_range_and_export_name(tmp_path: Path):
    """El worker conserva el tramo y el nombre elegidos por el diálogo de exportación."""
    command = editor_render.build_command(
        {'doc': 'x/project.json', 'format': 'mp3', 'start': 2, 'end': 5, 'name': 'demo-01'}, tmp_path
    )

    assert command == [
        sys.executable,
        '-m',
        'content_studio.editor.render_main',
        '--project',
        'x/project.json',
        '--format',
        'mp3',
        '--start',
        '2',
        '--end',
        '5',
        '--name',
        'demo-01',
        '--out-dir',
        str(tmp_path),
    ]
