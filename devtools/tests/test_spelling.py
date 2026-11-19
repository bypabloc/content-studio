"""`spelling`: cspell sobre identificadores, no sobre docstrings ni comentarios (spec 002, AC-1 y AC-2)."""

from __future__ import annotations

import json
import shutil

import pytest

from devtools import spelling
from devtools.__main__ import main as devtools

requiere_bun = pytest.mark.skipif(shutil.which('bun') is None, reason='bun no está instalado')


@requiere_bun
def test_ac2_identificadores_si_docstrings_y_comentarios_no(tmp_path):
    fuente = tmp_path / 'duracion.py'
    fuente.write_text(
        'def calcular_duracion():\n    """Calcula la duración."""\n    # pausa larga\n    return 1\n',
        encoding='utf-8',
    )
    palabras = {d.split(' ')[-1] for d in spelling.revisar([fuente])}
    assert {'calcular', 'duracion'} <= palabras
    assert not palabras & {'Calcula', 'calcula', 'pausa', 'larga', 'duración'}


@requiere_bun
def test_ac1_codigo_en_ingles_sale_0_y_json_con_issues_0(tmp_path, capsys):
    fuente = tmp_path / 'duration.py'
    fuente.write_text('def compute_duration():\n    """Compute the duration."""\n    return 1\n', encoding='utf-8')
    assert devtools(['spelling', str(fuente)]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == {'issues': 0, 'detalle': []}
