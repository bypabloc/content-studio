"""El kit de referencias propias: orden, duración, guion y nivel de la toma cruda (docs/scripts/README.md)."""

from __future__ import annotations

# Orden, duración (s) y guion con actitud de cada referencia (tabla de docs/scripts/README.md).
# neutral-fin solo existe en el kit propio: es una segunda toma neutral para el cierre, no un estilo de tts.
KIT = [
    ('neutral', 10, 12), ('friendly', 9, 11), ('expert', 10, 12), ('clear', 10, 12), ('steady', 10, 11),
    ('soft', 10, 11), ('energetic', 8, 10), ('dramatic', 10, 12), ('sad', 10, 12), ('intimate', 9, 11),
    ('neutral-en', 10, 12), ('neutral-end', 10, 12),
]  # fmt: skip
OPTIONAL = [('whisper', 7, 9)]
DURATION = {n: (lo, hi) for n, lo, hi in KIT + OPTIONAL}
SCRIPT = {
    'neutral': '00-neutral.md', 'friendly': '01-amistosa.md', 'soft': '02-suave.md', 'expert': '03-experta.md',
    'clear': '04-clara.md', 'steady': '05-estable.md', 'energetic': '06-energica.md', 'dramatic': '07-dramatica.md',
    'sad': '08-triste.md', 'intimate': '09-intima.md', 'neutral-en': '10-neutral-en.md',
    'neutral-end': '00-neutral.md', 'whisper': '09-intima.md',
}  # fmt: skip
# Criterios de la guía para la toma cruda: nivel y silencio digital. Los de la referencia final, en referencia.py.
LEVEL_DB = (-12.0, -6.0)
SILENCE_DB = -60.0

TIP = {
    'silence': 'No se oye nada: revisa el micrófono y el dispositivo elegido.',
    'bajo': 'Pico por debajo de −12 dB: acércate un poco al micrófono.',
    'alto': 'Pico por encima de −6 dB: aléjate un poco del micrófono.',
    'ok': 'Nivel dentro de la guía.',
}


def level_take(peak: float) -> str:
    """Estado del pico de la toma cruda frente a la guía (de -12 a -6 dB).

    >>> [level_take(p) for p in (-80.0, -20.0, -9.0, -3.0)]
    ['silence', 'bajo', 'ok', 'alto']
    """
    if peak <= SILENCE_DB:
        return 'silence'
    if peak < LEVEL_DB[0]:
        return 'bajo'
    if peak > LEVEL_DB[1]:
        return 'alto'
    return 'ok'
