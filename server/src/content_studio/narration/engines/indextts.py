"""IndexTTS 2.5: la emoción, con un clip de la voz (emociones/<nombre>.wav) o con su vector de 8 emociones."""

from __future__ import annotations

import os
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from content_studio import paths
from content_studio.narration.engines.base import TTSEngine, mark
from content_studio.narration.styles import EMOTIONS, normalize_vec

if TYPE_CHECKING:
    from content_studio.narration.blocks import References


@lru_cache
def load(code: Path, checkpoints: Path) -> Any:
    """Carga IndexTTS2 desde su código y su checkpoint."""
    sys.path.insert(0, str(code))
    # IndexTTS escribe checkpoints/hf_cache relativo al directorio actual: se fija antes de importarlo.
    os.environ['HF_HUB_CACHE'] = str(checkpoints / 'hf_cache')
    from indextts.infer_v2_5 import IndexTTS2

    return IndexTTS2(
        cfg_path=str(checkpoints / 'config.yaml'),
        model_dir=str(checkpoints),
        use_bf16=True,
        use_cuda_kernel=False,
        use_deepspeed=False,
        use_qwen_emo=False,
    )


CACHES = (load,)


class IndexTTS(TTSEngine):
    """Motor IndexTTS (narración)."""

    params = dict(max_text_tokens_per_segment=60)

    def emotion(self, pb: dict, name: str, intensity: float, refs: References) -> None:
        """Aplica la emoción con un audio de referencia, un vector o el texto."""
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
        """Genera el audio de los bloques con IndexTTS."""
        import soundfile as sf

        root = paths.engine_root('narration', self.spec.venv)
        assert self.spec.code is not None
        model = load(root / self.spec.code, root / self.spec.repo)
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
