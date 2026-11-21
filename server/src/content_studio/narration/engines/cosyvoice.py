"""CosyVoice 3: zero-shot con la transcripción de la referencia; la emoción, con instruct2."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from content_studio import paths
from content_studio.narration.engines.base import TTSEngine, mark
from content_studio.narration.styles import EMOTIONS

if TYPE_CHECKING:
    from content_studio.narration.blocks import References

SYSTEM = 'You are a helpful assistant.'  # prompt de sistema que CosyVoice 3 espera en zero-shot


@lru_cache
def load(code: Path, checkpoints: Path) -> Any:
    """Carga CosyVoice 3 desde su código y su checkpoint."""
    import soundfile as sf
    import torch
    import torchaudio

    sys.path[:0] = [str(code), str(code / 'third_party' / 'Matcha-TTS')]

    def leer_wav(
        path: str, *_a: object, **_k: object
    ) -> tuple:  # torchaudio 2.11 exige torchcodec; soundfile alcanza para WAV
        data, sr = sf.read(str(path), dtype='float32', always_2d=True)
        return torch.from_numpy(data.T.copy()), sr

    torchaudio.load = leer_wav
    from cosyvoice.cli.cosyvoice import AutoModel

    return AutoModel(model_dir=str(checkpoints))


CACHES = (load,)


class CosyVoice(TTSEngine):
    """Motor CosyVoice 3 (narración)."""

    intensity = False

    def mode(self, text_ref: str | None) -> str:
        """Modo de clonación: siempre zero-shot."""
        return 'zero_shot'

    def emotion(self, pb: dict, name: str, intensity: float, refs: References) -> None:
        """Aplica la emoción como instrucción de CosyVoice; sin instrucción, avisa."""
        if instruction := EMOTIONS[name]['cosy']:
            pb['emo'], pb['mode'], pb['emotion'] = {'instruction': instruction}, 'instruct2', mark(name, intensity)
        else:
            pb['notices'].append(f'cosyvoice3 does not follow "{name}"; generated without emotion')

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        """Genera el audio de los bloques con CosyVoice."""
        import torch

        root = paths.engine_root('narration', self.spec.venv, self.spec.name)
        assert self.spec.code is not None
        model = load(root / self.spec.code, root / self.spec.repo)
        audios = []
        for b in blocks:
            if b['emo']:  # instruct2: la instrucción reemplaza a la transcripción de la referencia
                prompt = f'{SYSTEM} {b["emo"]["instruction"]}<|endofprompt|>'
                parts = model.inference_instruct2(b['send'], prompt, str(b['ref']), stream=False, text_frontend=False)
            else:
                prompt = f'{SYSTEM}<|endofprompt|>{b["text_ref"]}'
                parts = model.inference_zero_shot(b['send'], prompt, str(b['ref']), stream=False, text_frontend=False)
            audios.append(torch.cat([j['tts_speech'] for j in parts], dim=1).squeeze(0).cpu().numpy())
        return audios, model.sample_rate
