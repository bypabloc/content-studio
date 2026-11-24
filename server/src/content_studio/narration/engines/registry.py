"""Los motores TTS disponibles. Solo stdlib: lo leen el parser y el CLI sin cargar torch.

Medido en RTX 4060 8 GB, bf16. Licencias en server/data/narration/README.md.
Orden de preferencia (así salen en los selectores de la API y de la app):
nota marca el ranking. Para agregar un motor: su archivo en engines/, una línea aquí y su venv.
"""

from __future__ import annotations

import sys

from content_studio.narration.engines.base import EngineSpec

_M = 'content_studio.narration.engines.'
ENGINES: dict[str, EngineSpec] = {
    'voxcpm2': EngineSpec(
        'voxcpm2',
        '.venv-voxcpm',
        _M + 'voxcpm',
        'VoxCPM',
        'Apache-2.0',
        True,
        'optional',
        30,
        'openbmb/VoxCPM2',
        note='★ recommended',
        recommended=True,
    ),
    'cosyvoice3': EngineSpec(
        'cosyvoice3',
        'engines/CosyVoice/.venv',
        _M + 'cosyvoice',
        'CosyVoice',
        'Apache-2.0 (card: "academic purposes")',
        True,
        'required',
        30,
        'engines/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B',
        code='engines/CosyVoice',
        note='2nd option',
    ),
    'qwen-1.7b': EngineSpec(
        'qwen-1.7b',
        '.venv-qwen',
        _M + 'qwen',
        'Qwen',
        'Apache-2.0',
        True,
        'optional',
        60,
        'Qwen/Qwen3-TTS-12Hz-1.7B-Base',
        weights=3.95,
        batch=True,
    ),
    'qwen-0.6b': EngineSpec(
        'qwen-0.6b',
        '.venv-qwen',
        _M + 'qwen',
        'Qwen',
        'Apache-2.0',
        True,
        'optional',
        60,
        'Qwen/Qwen3-TTS-12Hz-0.6B-Base',
        weights=2.06,
        batch=True,
    ),
    'chatterbox': EngineSpec(
        'chatterbox', '.venv-chatterbox', _M + 'chatterbox', 'Chatterbox', 'MIT', True, None, 10, 'v3'
    ),
    'omnivoice': EngineSpec(
        'omnivoice',
        '.venv-omnivoice',
        _M + 'omnivoice',
        'OmniVoice',
        'CC-BY-NC + Higgs Audio 2',
        False,
        'required',
        10,
        'k2-fsa/OmniVoice',
    ),
    'indextts': EngineSpec(
        'indextts',
        'engines/index-tts/.venv',
        _M + 'indextts',
        'IndexTTS',
        'bilibili Model Use License',
        False,
        None,
        15,
        'engines/index-tts/checkpoints',
        code='engines/index-tts',
    ),
}


def free_todo() -> None:
    """Descarga de la VRAM los modelos y prompts de los motores ya importados (antes de whisper y al regenerar)."""
    import gc

    import torch

    for mod in {sys.modules.get(e.module) for e in ENGINES.values()} - {None}:
        for f in mod.CACHES:
            f.cache_clear()
    gc.collect()
    torch.cuda.empty_cache()
