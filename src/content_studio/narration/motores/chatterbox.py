"""Chatterbox Multilingual V3: la emoción se pide con exaggeration y cfg_weight."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

from content_studio.narration.estilos import EMOCIONES
from content_studio.narration.motores.base import MotorTTS, marca

if TYPE_CHECKING:
    from content_studio.narration.bloques import Referencias


@lru_cache
def cargar(version: str) -> Any:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    return ChatterboxMultilingualTTS.from_pretrained(device='cuda', t3_model=version)


CACHES = (cargar,)


class Chatterbox(MotorTTS):
    def emocion(self, pb: dict, nombre: str, inten: float, refs: Referencias) -> None:
        if not EMOCIONES[nombre]['chatterbox']:
            pb['avisos'].append(f'chatterbox no tiene valores para "{nombre}"; usa [estilo: intima]')
            return
        k = inten / 0.6  # la tabla está medida a intensidad 0.6: a esa, los valores son los de la tabla
        ex, cfg = EMOCIONES[nombre]['chatterbox']
        ex, cfg = round(0.5 + (ex - 0.5) * k, 3), round(0.5 + (cfg - 0.5) * k, 3)
        pb['p'].update(exaggeration=ex, cfg_weight=cfg)
        pb['modo'], pb['emocion'] = 'parametros', {**marca(nombre, inten), 'exaggeration': ex, 'cfg_weight': cfg}

    def generar(self, bloques: list[dict], idioma: str) -> tuple[list, int]:
        modelo = cargar(self.espec.repo)
        audios = [
            modelo.generate(
                b['enviar'],
                language_id=idioma,
                audio_prompt_path=str(b['ref']),
                exaggeration=b['p']['exaggeration'],
                cfg_weight=b['p']['cfg_weight'],
                temperature=b['p']['temperature'],
            )
            .squeeze(0)
            .cpu()
            .numpy()
            for b in bloques
        ]
        return audios, modelo.sr
