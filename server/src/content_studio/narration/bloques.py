"""Lo que recibe el motor en cada bloque (§6): referencia, texto traducido, parámetros y control de emoción.

Lo común se resuelve aquí; lo propio de cada motor, en sus ganchos MotorTTS.modo() y MotorTTS.emocion().
"""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.narration.estilos import ESTILOS
from content_studio.narration.motores.base import MotorTTS
from content_studio.narration.texto.traducir import traducir


def resolver_ref(ref: Path, estilo: str) -> tuple[Path, str | None]:
    wav = ref / f'{estilo}.wav' if ref.is_dir() else ref
    if not wav.exists():
        sys.exit(f'No existe la referencia {wav}')
    txt = wav.with_suffix('.txt')
    return wav, txt.read_text(encoding='utf-8').strip() if txt.exists() else None


class Referencias:
    """Las referencias de cada estilo, resueltas y revisadas una sola vez: refs(estilo) -> (wav, transcripción)."""

    def __init__(self, motor: MotorTTS, ref: Path) -> None:
        self.motor, self.ref = motor, ref
        self.carpeta = ref if ref.is_dir() else ref.parent
        self.vistas: dict[str, tuple[Path, str | None]] = {}

    def tiene(self, estilo: str) -> bool:
        return self.ref.is_dir() and (self.ref / f'{estilo}.wav').exists()

    def __call__(self, estilo: str) -> tuple[Path, str | None]:
        if estilo not in self.vistas:
            import soundfile as sf

            e = self.motor.espec
            wav, txt = resolver_ref(self.ref, estilo)
            dur = sf.info(str(wav)).duration
            if dur > e.ref_max_s:
                print(f'Aviso: {wav.name} dura {dur:.1f} s; para {e.nombre} conviene hasta {e.ref_max_s} s.')
            if txt is None and e.txt == 'obligatorio':
                sys.exit(f'Falta {wav.with_suffix(".txt")}: {e.nombre} necesita la transcripción de la referencia.')
            if txt is None and e.txt == 'opcional':
                print(f'Aviso: falta {wav.with_suffix(".txt")}; {e.nombre} clona peor sin transcripción.')
            self.vistas[estilo] = (wav, txt)
        return self.vistas[estilo]


def preparar_bloques(motor: MotorTTS, segs: list[dict], ref: Path) -> list[dict]:
    """Un bloque por segmento. Si uno queda vacío tras traducir no se puede generar: se corta antes de empezar."""
    nombre = motor.espec.nombre
    refs = Referencias(motor, ref)
    pbs = []
    for i, b in enumerate(segs):
        envio, av = traducir(b['texto'], nombre)
        if not envio:
            sys.exit(f'El párrafo {i + 1} queda vacío para {nombre}: revisa sus marcas.')
        wav, txt = refs(b['estilo'])
        pb = dict(
            texto=b['texto'], estilo=b['estilo'], enviar=envio, ref=wav, texto_ref=txt, p=dict(ESTILOS[b['estilo']]),
            emo=None, emocion=None, modo=motor.modo(txt), avisos=b['avisos'] + av,
        )  # fmt: skip
        if b['emocion']:
            emo, inten = b['emocion']
            motor.emocion(pb, emo, inten, refs)
            if pb['emocion'] and inten != 0.6 and not motor.intensidad:
                pb['avisos'].append(f'{nombre} no controla la intensidad de la emoción; se ignora')
        pbs.append(pb)
    return pbs
