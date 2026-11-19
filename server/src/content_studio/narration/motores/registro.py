"""Los motores TTS disponibles. Solo stdlib: lo leen el parser y el CLI sin cargar torch.

Medido en RTX 4060 8 GB, bf16. Licencias en server/data/narration/README.md.
Orden de preferencia (así salen en el menú del
CLI): nota marca el ranking. Para agregar un motor: su archivo en motores/, una línea aquí y su venv.
"""

from __future__ import annotations

import sys

from content_studio.narration.motores.base import EspecMotor

_M = 'content_studio.narration.motores.'
MOTORES: dict[str, EspecMotor] = {
    'voxcpm2': EspecMotor(
        'voxcpm2',
        '.venv-voxcpm',
        _M + 'voxcpm',
        'VoxCPM',
        'Apache-2.0',
        True,
        'opcional',
        30,
        'openbmb/VoxCPM2',
        nota='★ recomendado',
    ),
    'cosyvoice3': EspecMotor(
        'cosyvoice3',
        'motores/CosyVoice/.venv',
        _M + 'cosyvoice',
        'CosyVoice',
        'Apache-2.0 (card: "academic purposes")',
        True,
        'obligatorio',
        30,
        'motores/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B',
        codigo='motores/CosyVoice',
        nota='2.ª opción',
    ),
    'qwen-1.7b': EspecMotor(
        'qwen-1.7b',
        '.venv-qwen',
        _M + 'qwen',
        'Qwen',
        'Apache-2.0',
        True,
        'opcional',
        60,
        'Qwen/Qwen3-TTS-12Hz-1.7B-Base',
        pesos=3.95,
        lote=True,
    ),
    'qwen-0.6b': EspecMotor(
        'qwen-0.6b',
        '.venv-qwen',
        _M + 'qwen',
        'Qwen',
        'Apache-2.0',
        True,
        'opcional',
        60,
        'Qwen/Qwen3-TTS-12Hz-0.6B-Base',
        pesos=2.06,
        lote=True,
    ),
    'chatterbox': EspecMotor(
        'chatterbox', '.venv-chatterbox', _M + 'chatterbox', 'Chatterbox', 'MIT', True, None, 10, 'v3'
    ),
    'omnivoice': EspecMotor(
        'omnivoice',
        '.venv-omnivoice',
        _M + 'omnivoice',
        'OmniVoice',
        'CC-BY-NC + Higgs Audio 2',
        False,
        'obligatorio',
        10,
        'k2-fsa/OmniVoice',
    ),
    'indextts': EspecMotor(
        'indextts',
        'motores/index-tts/.venv',
        _M + 'indextts',
        'IndexTTS',
        'bilibili Model Use License',
        False,
        None,
        15,
        'motores/index-tts/checkpoints',
        codigo='motores/index-tts',
    ),
}


def liberar_todo() -> None:
    """Descarga de la VRAM los modelos y prompts de los motores ya importados (antes de whisper y al regenerar)."""
    import gc

    import torch

    for mod in {sys.modules.get(e.modulo) for e in MOTORES.values()} - {None}:
        for f in mod.CACHES:
            f.cache_clear()
    gc.collect()
    torch.cuda.empty_cache()
