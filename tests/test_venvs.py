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


# La librería de cada motor, importada en su venv tras crear() (lo que el factory method carga ya dentro del venv).
LIBRERIAS = {
    'qwen-0.6b': 'qwen_tts',
    'chatterbox': 'chatterbox.mtl_tts',
    'omnivoice': 'omnivoice',
    'voxcpm2': 'voxcpm',
    'cosyvoice3': 'cosyvoice.cli.cosyvoice',
    'indextts': 'indextts.infer_v2_5',
    'acestep': 'acestep.handler',
    'heartmula': 'heartlib',
}


def _specs():
    from content_studio.music.motores.registro import MODELOS
    from content_studio.narration.motores.registro import MOTORES

    return {**MOTORES, **MODELOS}


@pytest.mark.local
@pytest.mark.parametrize('nombre', LIBRERIAS)
def test_importa_el_motor(nombre):
    e = _specs()[nombre]
    py = python_de(e.ruta_venv())
    if not py.exists():
        pytest.skip(f'{e.venv} no está instalado')
    rutas_codigo = []
    if getattr(e, 'codigo', None):
        d = rutas.NARRATION / e.codigo
        rutas_codigo = [str(d), str(d / 'third_party' / 'Matcha-TTS')]
    sonda = (
        f'import sys, importlib; sys.path[:0] = {rutas_codigo!r}\n'
        f'from content_studio.music.motores.registro import MODELOS\n'
        f'from content_studio.narration.motores.registro import MOTORES\n'
        f'm = {{**MOTORES, **MODELOS}}[{nombre!r}].crear()\n'
        f'importlib.import_module({LIBRERIAS[nombre]!r})\n'
        f'print(type(m).__name__)\n'
    )
    env = {
        **os.environ,
        'PYTHONPATH': str(rutas.SRC),
        'ACESTEP_PROJECT_ROOT': str(rutas.MUSIC / 'models' / 'ACE-Step-1.5'),
    }
    r = subprocess.run([str(py), '-c', sonda], capture_output=True, text=True, env=env, timeout=600, cwd=rutas.RAIZ)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.strip().splitlines()[-1] == e.clase
