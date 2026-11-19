"""IndexTTS 2.5: la emoción, con un clip de la voz (emociones/<nombre>.wav) o con su vector de 8 emociones."""

from __future__ import annotations

import os
import sys
import tempfile
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from content_studio import paths
from content_studio.narration.engines.base import TTSEngine, mark
from content_studio.narration.styles import EMOTIONS, normalize_vec

if TYPE_CHECKING:
    from content_studio.narration.blocks import References


@lru_cache
def load(code: str, ckpt: str) -> Any:
    sys.path.insert(0, str(paths.NARRATION / code))
    # IndexTTS escribe checkpoints/hf_cache relativo al directorio actual: se fija antes de importarlo.
    os.environ['HF_HUB_CACHE'] = str(paths.NARRATION / ckpt / 'hf_cache')
    from indextts.infer_v2_5 import IndexTTS2

    d = paths.NARRATION / ckpt
    return IndexTTS2(
        cfg_path=str(d / 'config.yaml'),
        model_dir=str(d),
        use_bf16=True,
        use_cuda_kernel=False,
        use_deepspeed=False,
        use_qwen_emo=False,
    )


CACHES = (load,)


class IndexTTS(TTSEngine):
    params = dict(max_text_tokens_per_segment=60)

    def emotion(self, pb: dict, name: str, intensity: float, refs: References) -> None:
        clip = refs.folder / 'emotions' / f'{name}.wav'
        if clip.exists():
            pb['emo'], pb['mode'], pb['emotion'] = {'clip': clip, 'alpha': intensity}, 'clip', mark(name, intensity)
        elif EMOTIONS[name]['vector']:
            vec = [0.0] * 8
            for j, val in EMOTIONS[name]['vector'].items():
                vec[j] = val
            pb['emo'] = {'vector': normalize_vec(vec), 'alpha': intensity}
            pb['mode'], pb['emotion'] = 'vector', mark(name, intensity)
        else:
            pb['notices'].append(f'IndexTTS has no vector for "{name}"; use [style: intimate]')

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        import soundfile as sf

        model = load(self.spec.code, self.spec.repo)
        audios = []
        for b in blocks:
            kw = dict(self.params)
            if b['emo']:
                kw['emo_alpha'] = b['emo']['alpha']
                if 'clip' in b['emo']:
                    kw['emo_audio_prompt'] = str(b['emo']['clip'])
                else:
                    kw['emo_vector'] = b['emo']['vector']
            fd, tmp = tempfile.mkstemp(suffix='.wav', dir='/dev/shm' if os.path.isdir('/dev/shm') else None)
            os.close(fd)
            try:
                model.infer(
                    spk_audio_prompt=str(b['ref']),
                    text=b['send'],
                    lang=language,
                    output_path=tmp,
                    verbose=False,
                    **kw,
                )
                audio, sr = sf.read(tmp, dtype='float32')
            finally:
                os.unlink(tmp)
            audios.append(audio if audio.ndim == 1 else audio.mean(axis=1))
        return audios, sr
