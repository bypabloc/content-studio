"""Los venvs de los motores de este equipo (marcador `local`, no corre en CI): process.use_venv relanza en cada

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
def test_relaunches_in_the_venv(venv, tmp_path):

    destination = paths.ROOT / venv

    if not python_de(destination).exists():
        pytest.skip(f'{venv} is not installed')

    probe = tmp_path / 'sonda.py'

    probe.write_text(
        'import sys, numpy, soundfile, content_studio.common.process as p\n'
        'print(sys.prefix, p.__file__, sys.argv[1:])\n',
        encoding='utf-8',
    )

    launch = (
        f'import sys; from pathlib import Path; from content_studio.common import process;'
        f'process.use_venv(Path(r"{destination}"), "su README", script=r"{probe}")'
    )

    env = {**os.environ, 'PYTHONPATH': str(paths.SRC)}

    r = subprocess.run([sys.executable, '-c', launch, 'arg 1'], capture_output=True, text=True, env=env, timeout=300)

    assert r.returncode == 0, r.stdout + r.stderr

    prefix, module, args = r.stdout.split(' ', 2)

    assert os.path.samefile(prefix, destination) and os.path.samefile(
        module, paths.SRC / 'content_studio/common/process.py'
    )

    assert args.strip() == "['arg 1']"


# La librería de cada motor, importada en su venv tras create() (lo que el factory method carga ya dentro del venv).

LIBRARIES = {
    'qwen-0.6b': 'qwen_tts',
    'chatterbox': 'chatterbox.mtl_tts',
    'omnivoice': 'omnivoice',
    'voxcpm2': 'voxcpm',
    'pyannote': 'pyannote.audio',
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
@pytest.mark.parametrize('name', LIBRARIES)
def test_imports_the_engine(name):

    e = _specs()[name]

    py = python_de(e.path_venv())

    if not py.exists():
        pytest.skip(f'{e.venv} is not installed')

    paths_code = []

    if getattr(e, 'code', None):
        d = paths.NARRATION / e.code

        paths_code = [str(d), str(d / 'third_party' / 'Matcha-TTS')]

    probe = (
        f'import sys, importlib; sys.path[:0] = {paths_code!r}\n'
        f'from content_studio.music.engines.registry import MODELS\n'
        f'from content_studio.narration.engines.registry import ENGINES\n'
        f'm = {{**ENGINES, **MODELS}}[{name!r}].create()\n'
        f'importlib.import_module({LIBRARIES[name]!r})\n'
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


@pytest.mark.local
def test_selected_engine_smoke(tmp_path):
    """La prueba de humo usa el mismo servicio; solo corre con un motor elegido explícitamente."""
    engine = os.environ.get('CONTENT_STUDIO_VERIFY_ENGINE')
    if not engine:
        pytest.skip('set CONTENT_STUDIO_VERIFY_ENGINE to run one real engine smoke test')

    from content_studio.engines.verification import verify_engine

    result = verify_engine(engine, tmp_path)

    assert result['ok'], result
    assert result['duration_s'] == pytest.approx(1, abs=0.05)
