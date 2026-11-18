"""OmniVoice (k2-fsa): la emoción, con la referencia del estilo que la representa (MotorTTS.emocion)."""

from __future__ import annotations

from functools import lru_cache

from content_studio.narration.motores.base import MotorTTS


@lru_cache
def cargar(repo):
    import torch
    from omnivoice import OmniVoice

    return OmniVoice.from_pretrained(repo, device_map='cuda', dtype=torch.float16)


@lru_cache
def prompt(modelo, ref, texto_ref):
    return modelo.create_voice_clone_prompt(ref_audio=ref, ref_text=texto_ref)


CACHES = (cargar, prompt)


class OmniVoice(MotorTTS):
    params = dict(num_step=32, guidance_scale=2.0)
    sugerir_evaluar = True

    def generar(self, bloques, idioma):
        modelo = cargar(self.espec.repo)
        audios = []
        for b in bloques:
            p = prompt(modelo, str(b['ref']), b['texto_ref'])
            audios.append(modelo.generate(text=b['enviar'], language=idioma, voice_clone_prompt=p, **self.params)[0])
        return audios, modelo.sampling_rate
