"""El registro de motores TTS apunta a los mismos venvs, repos y código que el tts.py viejo (moverlos rompe los venvs
o dispara descargas de varios GB), y la capa liviana se importa sin las dependencias pesadas."""

from __future__ import annotations

import os
import subprocess
import sys

from content_studio import rutas
from content_studio.narration.motores.registro import MOTORES

# Literales del MOTORES de narration/tts.py en dev 1fe463c, sin tocar.
VIEJO = {
    'voxcpm2': dict(venv='.venv-voxcpm', repo='openbmb/VoxCPM2', licencia='Apache-2.0', comercial=True,
                    txt='opcional', ref_max_s=30, nota='★ recomendado'),
    'cosyvoice3': dict(venv='motores/CosyVoice/.venv', codigo='motores/CosyVoice',
                       repo='motores/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B',
                       licencia='Apache-2.0 (card: "academic purposes")', comercial=True, txt='obligatorio',
                       ref_max_s=30, nota='2.ª opción'),
    'qwen-1.7b': dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-1.7B-Base', pesos=3.95, lote=True,
                      licencia='Apache-2.0', comercial=True, txt='opcional', ref_max_s=60),
    'qwen-0.6b': dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-0.6B-Base', pesos=2.06, lote=True,
                      licencia='Apache-2.0', comercial=True, txt='opcional', ref_max_s=60),
    'chatterbox': dict(venv='.venv-chatterbox', repo='v3', licencia='MIT', comercial=True, txt=None,
                       ref_max_s=10),
    'omnivoice': dict(venv='.venv-omnivoice', repo='k2-fsa/OmniVoice', licencia='CC-BY-NC + Higgs Audio 2',
                      comercial=False, txt='obligatorio', ref_max_s=10),
    'indextts': dict(venv='motores/index-tts/.venv', codigo='motores/index-tts', repo='motores/index-tts/checkpoints',
                     licencia='bilibili Model Use License', comercial=False, txt=None, ref_max_s=15),
}  # fmt: skip
LIVIANOS = [
    'content_studio.narration.parser', 'content_studio.narration.tts', 'content_studio.narration.bloques',
    'content_studio.narration.pipeline', 'content_studio.narration.metadatos',
    *{e.modulo for e in MOTORES.values()},
]  # fmt: skip


def test_registro_igual_al_viejo():
    assert list(MOTORES) == list(VIEJO)  # el orden es el del menú; el primero es el recomendado
    for nombre, campos in VIEJO.items():
        e = MOTORES[nombre]
        assert e.nombre == nombre
        assert {k: getattr(e, k) for k in campos} == campos, nombre
        assert e.ruta_venv() == rutas.RAIZ / 'narration' / campos['venv']


def test_crear_cada_motor_sin_cargarlo():
    for e in MOTORES.values():
        assert e.crear().espec is e


def test_imports_livianos():
    """Los módulos de narration se importan en un python sin torch, numpy ni soundfile (los mira el --help)."""
    pesadas = ['torch', 'torchaudio', 'numpy', 'soundfile', 'transformers', 'whisper', 'typer', 'rich', 'questionary']
    codigo = f'import sys\nfor p in {pesadas!r}:\n    sys.modules[p] = None\n' + ''.join(
        f'import {m}\n' for m in LIVIANOS
    )
    env = {**os.environ, 'PYTHONPATH': str(rutas.SRC)}
    r = subprocess.run([sys.executable, '-c', codigo], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
