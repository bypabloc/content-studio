"""VoxCPM2: Hi-Fi con la transcripción de la referencia; la emoción va como instrucción en el texto."""

from __future__ import annotations

from functools import lru_cache

from content_studio.narration.estilos import EMOCIONES
from content_studio.narration.motores.base import MotorTTS, marca


@lru_cache
def cargar(repo):
    from voxcpm import VoxCPM

    return VoxCPM.from_pretrained(repo, load_denoiser=False, optimize=False)


CACHES = (cargar,)


class VoxCPM(MotorTTS):
    params = dict(cfg_value=2.0, inference_timesteps=10, retry_badcase_max_times=1)
    intensidad = False

    def modo(self, texto_ref):
        return 'hifi' if texto_ref else 'clonacion'

    def emocion(self, pb, nombre, inten, refs):
        pb['enviar'] = f'({EMOCIONES[nombre]["voxcpm"]}){pb["enviar"]}'  # la instrucción va en el texto
        pb['texto_ref'], pb['modo'], pb['emocion'] = None, 'controlable', marca(nombre, inten)  # con Hi-Fi se leería

    def generar(self, bloques, idioma):
        modelo = cargar(self.espec.repo)
        audios = []
        for b in bloques:
            kw = dict(
                reference_wav_path=str(b['ref']), max_len=min(4096, max(256, len(b['enviar']) * 6)), **self.params
            )
            if b['texto_ref']:  # Hi-Fi. Con emoción (controlable) no va la transcripción: se leería la instrucción
                kw.update(prompt_wav_path=str(b['ref']), prompt_text=b['texto_ref'])
            audios.append(modelo.generate(text=b['enviar'], **kw))
        return audios, modelo.tts_model.sample_rate
