"""Servicio `clean.render` de la cola (spec 013, D-4): valida el render y arma el comando de `render_main`."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.services import clean_render


def test_the_render_runs_on_the_cpu():
    """El render es ffmpeg: no carga modelos, así que va por CPU y no toma el candado de la GPU."""
    assert clean_render.RESOURCE == 'cpu'


def test_validate_requires_the_source_and_the_analysis_folder():
    """Hacen falta el archivo original y la carpeta del análisis con su cuts.json."""
    errors = clean_render.validate({'input': '', 'analysis': ''})

    assert {e['code'] for e in errors} == {'missing_input', 'missing_analysis'}


def test_build_command_passes_the_analysis_folder_and_the_output_folder(tmp_path: Path):
    """El comando corre `render_main` con el origen, la carpeta del análisis y la de salida del trabajo."""
    command = clean_render.build_command({'input': 'a.mp4', 'analysis': 'x/analisis'}, tmp_path)

    assert command[0] == sys.executable
    assert command[1:3] == ['-m', 'content_studio.clean.render_main']
    options = dict(zip(command[3::2], command[4::2], strict=False))
    assert options == {'--input': 'a.mp4', '--analysis': 'x/analisis', '--out': str(tmp_path)}
