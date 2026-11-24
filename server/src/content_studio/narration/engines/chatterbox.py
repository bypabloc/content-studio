"""Chatterbox Multilingual V3: la emoción se pide con exaggeration y cfg_weight."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from content_studio.narration.engines.base import TTSEngine, mark
from content_studio.narration.styles import EMOTIONS

if TYPE_CHECKING:
    from content_studio.narration.blocks import References


@lru_cache
def load(version: str) -> Any:
    """Carga el modelo Chatterbox desde Hugging Face, en GPU."""
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    return ChatterboxMultilingualTTS.from_pretrained(device='cuda', t3_model=version)


CACHES = (load,)


class Chatterbox(TTSEngine):
    """Motor Chatterbox (narración)."""

    def emotion(self, pb: dict, name: str, intensity: float, refs: References) -> None:
        """Aplica la emoción con los valores medidos de Chatterbox."""
        if not EMOTIONS[name]['chatterbox']:
            pb['notices'].append(f'chatterbox has no values for "{name}"; use [style: intimate]')
            return
        k = intensity / 0.6  # la tabla está medida a intensidad 0.6: a esa, los valores son los de la tabla
        ex, cfg = EMOTIONS[name]['chatterbox']
        ex, cfg = round(0.5 + (ex - 0.5) * k, 3), round(0.5 + (cfg - 0.5) * k, 3)
        pb['p'].update(exaggeration=ex, cfg_weight=cfg)
        pb['mode'], pb['emotion'] = 'params', {**mark(name, intensity), 'exaggeration': ex, 'cfg_weight': cfg}

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        """Genera el audio de los bloques con Chatterbox."""
        model = load(self.spec.repo)
        audios = [
            model.generate(
                b['send'],
                language_id=language,
                audio_prompt_path=str(b['ref']),
                exaggeration=b['p']['exaggeration'],
                cfg_weight=b['p']['cfg_weight'],
                temperature=b['p']['temperature'],
            )
            .squeeze(0)
            .cpu()
            .numpy()
            for b in blocks
        ]
        return audios, model.sr
