"""CosyVoice 3: zero-shot con la transcripción de la referencia; la emoción, con instruct2."""

from __future__ import annotations

import sys
from functools import lru_cache

from content_studio import rutas
from content_studio.narration.estilos import EMOCIONES
from content_studio.narration.motores.base import MotorTTS, marca

SISTEMA = 'You are a helpful assistant.'  # prompt de sistema que CosyVoice 3 espera en zero-shot


@lru_cache
def cargar(codigo, ckpt):
    import soundfile as sf
    import torch
    import torchaudio

    d = rutas.NARRATION / codigo
    sys.path[:0] = [str(d), str(d / 'third_party' / 'Matcha-TTS')]

    def leer_wav(path, *_a, **_k):  # torchaudio 2.11 exige torchcodec; soundfile alcanza para WAV
        data, sr = sf.read(str(path), dtype='float32', always_2d=True)
        return torch.from_numpy(data.T.copy()), sr

    torchaudio.load = leer_wav
    from cosyvoice.cli.cosyvoice import AutoModel

    return AutoModel(model_dir=str(rutas.NARRATION / ckpt))


CACHES = (cargar,)


class CosyVoice(MotorTTS):
    intensidad = False

    def modo(self, texto_ref):
        return 'zero_shot'

    def emocion(self, pb, nombre, inten, refs):
        if instruccion := EMOCIONES[nombre]['cosy']:
            pb['emo'], pb['modo'], pb['emocion'] = {'instruccion': instruccion}, 'instruct2', marca(nombre, inten)
        else:
            pb['avisos'].append(f'cosyvoice3 no sigue "{nombre}"; se genera sin emoción')

    def generar(self, bloques, idioma):
        import torch

        modelo = cargar(self.espec.codigo, self.espec.repo)
        audios = []
        for b in bloques:
            if b['emo']:  # instruct2: la instrucción reemplaza a la transcripción de la referencia
                prompt = f'{SISTEMA} {b["emo"]["instruccion"]}<|endofprompt|>'
                partes = modelo.inference_instruct2(
                    b['enviar'], prompt, str(b['ref']), stream=False, text_frontend=False
                )
            else:
                prompt = f'{SISTEMA}<|endofprompt|>{b["texto_ref"]}'
                partes = modelo.inference_zero_shot(
                    b['enviar'], prompt, str(b['ref']), stream=False, text_frontend=False
                )
            audios.append(torch.cat([j['tts_speech'] for j in partes], dim=1).squeeze(0).cpu().numpy())
        return audios, modelo.sample_rate
