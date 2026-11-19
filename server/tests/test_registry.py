"""El registro de motores TTS apunta a los mismos venvs, repos y código que el tts.py viejo (moverlos rompe los venvs

o dispara descargas de varios GB), y la capa liviana se importa sin las dependencias pesadas."""

from __future__ import annotations

import os
import subprocess
import sys

from content_studio import paths
from content_studio.narration.engines.registry import ENGINES

# Literales del MOTORES de narration/tts.py en dev 1fe463c (antes de la 001), sin tocar.

OLD = {

    'voxcpm2': dict(venv='.venv-voxcpm', repo='openbmb/VoxCPM2', license='Apache-2.0', commercial=True,

                    txt='optional', ref_max_s=30, note='★ recommended'),

    'cosyvoice3': dict(venv='engines/CosyVoice/.venv', code='engines/CosyVoice',

                       repo='engines/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B',

                       license='Apache-2.0 (card: "academic purposes")', commercial=True, txt='required',

                       ref_max_s=30, note='2nd option'),

    'qwen-1.7b': dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-1.7B-Base', weights=3.95, batch=True,

                      license='Apache-2.0', commercial=True, txt='optional', ref_max_s=60),

    'qwen-0.6b': dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-0.6B-Base', weights=2.06, batch=True,

                      license='Apache-2.0', commercial=True, txt='optional', ref_max_s=60),

    'chatterbox': dict(venv='.venv-chatterbox', repo='v3', license='MIT', commercial=True, txt=None,

                       ref_max_s=10),

    'omnivoice': dict(venv='.venv-omnivoice', repo='k2-fsa/OmniVoice', license='CC-BY-NC + Higgs Audio 2',

                      commercial=False, txt='required', ref_max_s=10),

    'indextts': dict(venv='engines/index-tts/.venv', code='engines/index-tts', repo='engines/index-tts/checkpoints',

                     license='bilibili Model Use License', commercial=False, txt=None, ref_max_s=15),

}  # fmt: skip

LIGHT = [

    'content_studio.narration.parser', 'content_studio.narration.tts', 'content_studio.narration.blocks',

    'content_studio.narration.pipeline', 'content_studio.narration.metadata',

    *{e.module for e in ENGINES.values()},

]  # fmt: skip


def test_registry_equal_al_old():

    assert list(ENGINES) == list(OLD)  # el orden es el del menú; el primero es el recomendado

    for name, fields in OLD.items():
        e = ENGINES[name]

        assert e.name == name

        assert {k: getattr(e, k) for k in fields} == fields, name

        assert e.path_venv() == paths.NARRATION / fields['venv']


def test_create_each_engine_without_loading_it():

    for e in ENGINES.values():
        assert e.create().spec is e


def test_imports_light_modules():
    """Los módulos de narration se importan en un python sin torch, numpy ni soundfile (los mira el --help)."""

    heavy = ['torch', 'torchaudio', 'numpy', 'soundfile', 'transformers', 'whisper', 'typer', 'rich', 'questionary']

    code = f'import sys\nfor p in {heavy!r}:\n    sys.modules[p] = None\n' + ''.join(f'import {m}\n' for m in LIGHT)

    env = {**os.environ, 'PYTHONPATH': str(paths.SRC)}

    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env)

    assert r.returncode == 0, r.stderr
