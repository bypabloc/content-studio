"""IndexTTS 2.5: la emoción, con un clip de la voz (emociones/<nombre>.wav) o con su vector de 8 emociones."""

from __future__ import annotations

import os
import sys
import tempfile
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from content_studio import rutas
from content_studio.narration.estilos import EMOCIONES, normalizar_vec
from content_studio.narration.motores.base import MotorTTS, marca

if TYPE_CHECKING:
    from content_studio.narration.bloques import Referencias


@lru_cache
def cargar(codigo: str, ckpt: str) -> Any:
    sys.path.insert(0, str(rutas.NARRATION / codigo))
    # IndexTTS escribe checkpoints/hf_cache relativo al directorio actual: se fija antes de importarlo.
    os.environ['HF_HUB_CACHE'] = str(rutas.NARRATION / ckpt / 'hf_cache')
    from indextts.infer_v2_5 import IndexTTS2

    d = rutas.NARRATION / ckpt
    return IndexTTS2(
        cfg_path=str(d / 'config.yaml'),
        model_dir=str(d),
        use_bf16=True,
        use_cuda_kernel=False,
        use_deepspeed=False,
        use_qwen_emo=False,
    )


CACHES = (cargar,)


class IndexTTS(MotorTTS):
    params = dict(max_text_tokens_per_segment=60)

    def emocion(self, pb: dict, nombre: str, inten: float, refs: Referencias) -> None:
        clip = refs.carpeta / 'emociones' / f'{nombre}.wav'
        if clip.exists():
            pb['emo'], pb['modo'], pb['emocion'] = {'clip': clip, 'alpha': inten}, 'clip', marca(nombre, inten)
        elif EMOCIONES[nombre]['vector']:
            vec = [0.0] * 8
            for j, val in EMOCIONES[nombre]['vector'].items():
                vec[j] = val
            pb['emo'] = {'vector': normalizar_vec(vec), 'alpha': inten}
            pb['modo'], pb['emocion'] = 'vector', marca(nombre, inten)
        else:
            pb['avisos'].append(f'IndexTTS no tiene vector para "{nombre}"; usa [estilo: intima]')

    def generar(self, bloques: list[dict], idioma: str) -> tuple[list, int]:
        import soundfile as sf

        modelo = cargar(self.espec.codigo, self.espec.repo)
        audios = []
        for b in bloques:
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
                modelo.infer(
                    spk_audio_prompt=str(b['ref']), text=b['enviar'], lang=idioma, output_path=tmp, verbose=False, **kw
                )
                audio, sr = sf.read(tmp, dtype='float32')
            finally:
                os.unlink(tmp)
            audios.append(audio if audio.ndim == 1 else audio.mean(axis=1))
        return audios, sr
