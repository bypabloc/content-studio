"""Servicio `clean.analyze` de la cola (spec 013, D-4): valida el pedido y arma el comando de `analyze_main`."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.services import clean_analyze

PARAMS = {'input': 'a.mp4', 'model': 'small', 'language': 'es', 'min_gap': 0.5, 'padding': 0.15, 'edges': True}


def test_the_analysis_runs_on_the_gpu_lock():
    """Transcribe carga el modelo: la cola lo corre con el candado de la GPU."""
    assert clean_analyze.RESOURCE == 'gpu'


def test_validate_accepts_a_complete_request():
    """Un pedido con modelo, idioma y parámetros válidos no da errores."""
    assert clean_analyze.validate(PARAMS) == []


def test_validate_names_a_missing_input():
    """Sin archivo de entrada da `missing_input`."""
    errors = clean_analyze.validate({**PARAMS, 'input': ''})

    assert errors == [{'code': 'missing_input', 'params': {}}]


def test_validate_rejects_a_negative_gap():
    """El hueco mínimo y el margen no pueden ser negativos: `invalid_gap`."""
    errors = clean_analyze.validate({**PARAMS, 'min_gap': -1.0})

    assert errors == [{'code': 'invalid_gap', 'params': {}}]


def test_build_command_passes_the_gap_padding_and_edges_to_analyze_main(tmp_path: Path):
    """El comando corre `analyze_main` con los parámetros del corte y la carpeta del trabajo."""
    command = clean_analyze.build_command(PARAMS, tmp_path)

    assert command[0] == sys.executable
    assert command[1:3] == ['-m', 'content_studio.clean.analyze_main']
    options = dict(zip(command[3::2], command[4::2], strict=False))
    assert options['--min-gap'] == '0.5'
    assert options['--padding'] == '0.15'
    assert options['--folder'] == str(tmp_path)
    assert '--edges' in command


def test_ac8_build_command_passes_diarize_to_analyze_main(tmp_path: Path):
    """AC-8: con «Identificar hablantes», el comando de analyze_main lleva --diarize; sin él, no."""
    assert '--diarize' in clean_analyze.build_command({**PARAMS, 'diarize': True}, tmp_path)
    assert '--diarize' not in clean_analyze.build_command(PARAMS, tmp_path)
