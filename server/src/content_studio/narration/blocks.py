"""Lo que recibe el motor en cada bloque (§6): referencia, texto traducido, parámetros y control de emoción.

Lo común se resuelve aquí; lo propio de cada motor, en sus ganchos MotorTTS.modo() y MotorTTS.emocion().
"""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.narration.engines.base import TTSEngine
from content_studio.narration.styles import STYLES
from content_studio.narration.text.translate import translate


def resolve_ref(ref: Path, style: str) -> tuple[Path, str | None]:
    """Ruta de la referencia y su transcripción para un estilo; sale si el audio no existe."""
    wav = ref / f'{style}.wav' if ref.is_dir() else ref
    if not wav.exists():
        sys.exit(f'The reference does not exist: {wav}')
    txt = wav.with_suffix('.txt')
    return wav, txt.read_text(encoding='utf-8').strip() if txt.exists() else None


class References:
    """Las referencias de cada estilo, resueltas y revisadas una sola vez: refs(estilo) -> (wav, transcripción)."""

    def __init__(self, engine: TTSEngine, ref: Path) -> None:
        """Carga las referencias de un motor; `ref` puede ser una carpeta o un audio."""
        self.engine, self.ref = engine, ref
        self.folder = ref if ref.is_dir() else ref.parent
        self.views: dict[str, tuple[Path, str | None]] = {}

    def has(self, style: str) -> bool:
        """True si la carpeta de referencia tiene el audio de `style`."""
        return self.ref.is_dir() and (self.ref / f'{style}.wav').exists()

    def __call__(self, style: str) -> tuple[Path, str | None]:
        """Devuelve la referencia (audio, transcripción) de `style`; la prepara la primera vez."""
        if style not in self.views:
            import soundfile as sf

            e = self.engine.spec
            wav, txt = resolve_ref(self.ref, style)
            dur = sf.info(str(wav)).duration
            if dur > e.ref_max_s:
                print(f'Notice: {wav.name} lasts {dur:.1f} s; for {e.name} use up to {e.ref_max_s} s.')
            if txt is None and e.txt == 'required':
                sys.exit(f'Missing {wav.with_suffix(".txt")}: {e.name} needs the reference transcript.')
            if txt is None and e.txt == 'optional':
                print(f'Notice: missing {wav.with_suffix(".txt")}; {e.name} clones worse without a transcript.')
            self.views[style] = (wav, txt)
        return self.views[style]


def prepare_blocks(engine: TTSEngine, secs: list[dict], ref: Path) -> list[dict]:
    """Un bloque por segmento. Si uno queda vacío tras traducir no se puede generar: se corta antes de empezar."""
    name = engine.spec.name
    refs = References(engine, ref)
    pbs = []
    for i, b in enumerate(secs):
        send, av = translate(b['text'], name)
        if not send:
            sys.exit(f'Paragraph {i + 1} is empty for {name}: check its marks.')
        wav, txt = refs(b['style'])
        pb = dict(
            text=b['text'], style=b['style'], send=send, ref=wav, text_ref=txt, p=dict(STYLES[b['style']]),
            emo=None, emotion=None, mode=engine.mode(txt), notices=b['notices'] + av,
        )  # fmt: skip
        if b['emotion']:
            emo, intensity = b['emotion']
            engine.emotion(pb, emo, intensity, refs)
            if pb['emotion'] and intensity != 0.6 and not engine.intensity:
                pb['notices'].append(f'{name} does not control emotion intensity; ignored')
        pbs.append(pb)
    return pbs
