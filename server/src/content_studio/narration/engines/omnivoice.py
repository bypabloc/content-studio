"""OmniVoice (k2-fsa): la emoción, con la referencia del estilo que la representa (MotorTTS.emocion)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from content_studio.narration.engines.base import TTSEngine


@lru_cache
def load(repo: str) -> Any:
    """Carga OmniVoice desde Hugging Face, en GPU."""
    import torch
    from omnivoice import OmniVoice

    return OmniVoice.from_pretrained(repo, device_map='cuda', dtype=torch.float16)


@lru_cache
def prompt(model: Any, ref: str, text_ref: str | None) -> Any:
    """Prompt de clonación de una voz con su transcripción."""
    return model.create_voice_clone_prompt(ref_audio=ref, ref_text=text_ref)


CACHES = (load, prompt)


class OmniVoice(TTSEngine):
    """Motor OmniVoice (narración)."""

    params = dict(num_step=32, guidance_scale=2.0)
    suggest_evaluate = True

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        """Genera el audio de los bloques con OmniVoice."""
        model = load(self.spec.repo)
        audios = []
        for b in blocks:
            p = prompt(model, str(b['ref']), b['text_ref'])
            audios.append(model.generate(text=b['send'], language=language, voice_clone_prompt=p, **self.params)[0])
        return audios, model.sampling_rate
