"""Qwen3-TTS (1.7B y 0.6B, la misma clase): genera varias frases de la misma referencia por pasada."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from content_studio.narration.engines.base import TTSEngine

LANGUAGE = {'es': 'Spanish', 'en': 'English'}


@lru_cache
def load(repo: str) -> Any:
    import torch
    from qwen_tts import Qwen3TTSModel

    return Qwen3TTSModel.from_pretrained(repo, device_map='cuda:0', dtype=torch.bfloat16)


@lru_cache
def prompt(model: Any, ref: str, text_ref: str | None) -> Any:
    return model.create_voice_clone_prompt(ref_audio=ref, ref_text=text_ref, x_vector_only_mode=text_ref is None)


CACHES = (load, prompt)


class Qwen(TTSEngine):
    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        model = load(self.spec.repo)
        b = blocks[0]  # pipeline.lotes() agrupa bloques con la misma referencia y temperatura
        p = prompt(model, str(b['ref']), b['text_ref'])
        return model.generate_voice_clone(
            text=[x['send'] for x in blocks],
            language=[LANGUAGE[language]] * len(blocks),
            voice_clone_prompt=p * len(blocks),
            temperature=b['p']['temperature'],
        )
