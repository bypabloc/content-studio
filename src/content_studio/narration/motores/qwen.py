"""Qwen3-TTS (1.7B y 0.6B, la misma clase): genera varias frases de la misma referencia por pasada."""

from __future__ import annotations

from functools import lru_cache

from content_studio.narration.motores.base import MotorTTS

IDIOMA = {'es': 'Spanish', 'en': 'English'}


@lru_cache
def cargar(repo):
    import torch
    from qwen_tts import Qwen3TTSModel

    return Qwen3TTSModel.from_pretrained(repo, device_map='cuda:0', dtype=torch.bfloat16)


@lru_cache
def prompt(modelo, ref, texto_ref):
    return modelo.create_voice_clone_prompt(ref_audio=ref, ref_text=texto_ref, x_vector_only_mode=texto_ref is None)


CACHES = (cargar, prompt)


class Qwen(MotorTTS):
    def generar(self, bloques, idioma):
        modelo = cargar(self.espec.repo)
        b = bloques[0]  # pipeline.lotes() agrupa bloques con la misma referencia y temperatura
        p = prompt(modelo, str(b['ref']), b['texto_ref'])
        return modelo.generate_voice_clone(
            text=[x['enviar'] for x in bloques],
            language=[IDIOMA[idioma]] * len(bloques),
            voice_clone_prompt=p * len(bloques),
            temperature=b['p']['temperature'],
        )
