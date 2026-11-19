"""Los venvs de los motores de este equipo (marcador `local`, no corre en CI): proceso.usar_venv relanza en cada

uno, el hijo ve src/ por PYTHONPATH e importa numpy y soundfile. Corre con: uv run pytest -m local"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from content_studio import paths
from content_studio.common.process import python_de

VENVS = [
    'server/data/narration/.venv-qwen',
    'server/data/narration/.venv-chatterbox',
    'server/data/narration/.venv-omnivoice',
    'server/data/narration/.venv-voxcpm',
    'server/data/narration/engines/CosyVoice/.venv',
    'server/data/narration/engines/index-tts/.venv',
    'server/data/music/.venv-acestep',
    'server/data/music/.venv-heartmula',
]


@pytest.mark.local
@pytest.mark.parametrize('venv', VENVS)
def test_relanza_en_el_venv(venv, tmp_path):

    destination = paths.ROOT / venv

    if not python_de(destination).exists():
        pytest.skip(f'{venv} no está instalado')

    probe = tmp_path / 'sonda.py'

    probe.write_text(
        'import sys, numpy, soundfile, content_studio.common.process as p\n'
        'print(sys.prefix, p.__file__, sys.argv[1:])\n',
        encoding='utf-8',
    )

    lanzar = (
        f'import sys; from pathlib import Path; from content_studio.common import proceso; '
        f'proceso.usar_venv(Path(r"{destination}"), "su README", script=r"{probe}")'
    )

    env = {**os.environ, 'PYTHONPATH': str(paths.SRC)}

    r = subprocess.run([sys.executable, '-c', lanzar, 'arg 1'], capture_output=True, text=True, env=env, timeout=300)

    assert r.returncode == 0, r.stdout + r.stderr

    prefix, module, args = r.stdout.split(' ', 2)

    assert os.path.samefile(prefix, destination) and os.path.samefile(
        module, paths.SRC / 'content_studio/comun/proceso.py'
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

    from content_studio.music.engines.registry import MODELS
    from content_studio.narration.engines.registry import ENGINES

    return {**ENGINES, **MODELS}


@pytest.mark.local
@pytest.mark.parametrize('name', LIBRERIAS)
def test_importa_el_engine(name):

    e = _specs()[name]

    py = python_de(e.path_venv())

    if not py.exists():
        pytest.skip(f'{e.venv} no está instalado')

    paths_code = []

    if getattr(e, 'code', None):
        d = paths.NARRATION / e.code

        paths_code = [str(d), str(d / 'third_party' / 'Matcha-TTS')]

    probe = (
        f'import sys, importlib; sys.path[:0] = {paths_code!r}\n'
        f'from content_studio.music.engines.registry import MODELOS\n'
        f'from content_studio.narration.engines.registry import MOTORES\n'
        f'm = {{**MOTORES, **MODELOS}}[{name!r}].crear()\n'
        f'importlib.import_module({LIBRERIAS[name]!r})\n'
        f'print(type(m).__name__)\n'
    )

    env = {
        **os.environ,
        'PYTHONPATH': str(paths.SRC),
        'ACESTEP_PROJECT_ROOT': str(paths.MUSIC / 'models' / 'ACE-Step-1.5'),
    }

    r = subprocess.run([str(py), '-c', probe], capture_output=True, text=True, env=env, timeout=600, cwd=paths.ROOT)

    assert r.returncode == 0, r.stdout + r.stderr

    assert r.stdout.strip().splitlines()[-1] == e.kind
