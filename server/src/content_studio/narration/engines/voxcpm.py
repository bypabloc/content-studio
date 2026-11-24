"""VoxCPM2: Hi-Fi con la transcripción de la referencia; la emoción va como instrucción en el texto."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from content_studio.narration.engines.base import TTSEngine, mark
from content_studio.narration.styles import EMOTIONS

if TYPE_CHECKING:
    from content_studio.narration.blocks import References


@lru_cache
def load(repo: str) -> Any:
    """Carga VoxCPM desde Hugging Face."""
    from voxcpm import VoxCPM

    return VoxCPM.from_pretrained(repo, load_denoiser=False, optimize=False)


CACHES = (load,)


class VoxCPM(TTSEngine):
    """Motor VoxCPM (narración)."""

    params = dict(cfg_value=2.0, inference_timesteps=10, retry_badcase_max_times=1)
    intensity = False

    def mode(self, text_ref: str | None) -> str:
        """Modo de clonación: Hi-Fi con transcripción; sin ella, clonación."""
        return 'hifi' if text_ref else 'cloning'

    def emotion(self, pb: dict, name: str, intensity: float, refs: References) -> None:
        """Aplica la emoción como instrucción en el texto."""
        pb['send'] = f'({EMOTIONS[name]["voxcpm"]}){pb["send"]}'  # la instrucción va en el texto
        pb['text_ref'], pb['mode'], pb['emotion'] = None, 'controllable', mark(name, intensity)  # con Hi-Fi se leería

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        """Genera el audio de los bloques con VoxCPM."""
        model = load(self.spec.repo)
        audios = []
        for b in blocks:
            kw = dict(reference_wav_path=str(b['ref']), max_len=min(4096, max(256, len(b['send']) * 6)), **self.params)
            if b['text_ref']:  # Hi-Fi. Con emoción (controlable) no va la transcripción: se leería la instrucción
                kw.update(prompt_wav_path=str(b['ref']), prompt_text=b['text_ref'])
            audios.append(model.generate(text=b['send'], **kw))
        return audios, model.tts_model.sample_rate
