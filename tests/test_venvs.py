"""Los venvs de los motores de este equipo (marcador `local`, no corre en CI): proceso.usar_venv relanza en cada
uno, el hijo ve src/ por PYTHONPATH e importa numpy y soundfile. Corre con: uv run pytest -m local"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from content_studio import rutas
from content_studio.comun.proceso import python_de

VENVS = [
    'narration/.venv-qwen',
    'narration/.venv-chatterbox',
    'narration/.venv-omnivoice',
    'narration/.venv-voxcpm',
    'narration/motores/CosyVoice/.venv',
    'narration/motores/index-tts/.venv',
    'music/.venv-acestep',
    'music/.venv-heartmula',
]


@pytest.mark.local
@pytest.mark.parametrize('venv', VENVS)
def test_relanza_en_el_venv(venv, tmp_path):
    destino = rutas.RAIZ / venv
    if not python_de(destino).exists():
        pytest.skip(f'{venv} no está instalado')
    sonda = tmp_path / 'sonda.py'
    sonda.write_text(
        'import sys, numpy, soundfile, content_studio.comun.proceso as p\n'
        'print(sys.prefix, p.__file__, sys.argv[1:])\n',
        encoding='utf-8',
    )
    lanzar = (
        f'import sys; from pathlib import Path; from content_studio.comun import proceso; '
        f'proceso.usar_venv(Path(r"{destino}"), "su README", script=r"{sonda}")'
    )
    env = {**os.environ, 'PYTHONPATH': str(rutas.SRC)}
    r = subprocess.run([sys.executable, '-c', lanzar, 'arg 1'], capture_output=True, text=True, env=env, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    prefijo, modulo, args = r.stdout.split(' ', 2)
    assert os.path.samefile(prefijo, destino) and os.path.samefile(
        modulo, rutas.SRC / 'content_studio/comun/proceso.py'
    )
    assert args.strip() == "['arg 1']"
