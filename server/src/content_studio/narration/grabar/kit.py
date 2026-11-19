"""El kit de referencias propias: orden, duración, guion y nivel de la toma cruda (docs/guiones/README.md)."""

from __future__ import annotations

# Orden, duración (s) y guion con actitud de cada referencia (tabla de docs/guiones/README.md).
# neutral-fin solo existe en el kit propio: es una segunda toma neutral para el cierre, no un estilo de tts.
KIT = [
    ('neutral', 10, 12), ('amistosa', 9, 11), ('experta', 10, 12), ('clara', 10, 12), ('estable', 10, 11),
    ('suave', 10, 11), ('energica', 8, 10), ('dramatica', 10, 12), ('triste', 10, 12), ('intima', 9, 11),
    ('neutral-en', 10, 12), ('neutral-fin', 10, 12),
]  # fmt: skip
OPCIONAL = [('susurro', 7, 9)]
DURACION = {n: (lo, hi) for n, lo, hi in KIT + OPCIONAL}
GUION = {
    'neutral': '00-neutral.md', 'amistosa': '01-amistosa.md', 'suave': '02-suave.md', 'experta': '03-experta.md',
    'clara': '04-clara.md', 'estable': '05-estable.md', 'energica': '06-energica.md', 'dramatica': '07-dramatica.md',
    'triste': '08-triste.md', 'intima': '09-intima.md', 'neutral-en': '10-neutral-en.md',
    'neutral-fin': '00-neutral.md', 'susurro': '09-intima.md',
}  # fmt: skip
# Criterios de la guía para la toma cruda: nivel y silencio digital. Los de la referencia final, en referencia.py.
NIVEL_DB = (-12.0, -6.0)
SILENCIO_DB = -60.0

CONSEJO = {
    'silencio': 'No se oye nada: revisa el micrófono y el dispositivo elegido.',
    'bajo': 'Pico por debajo de −12 dB: acércate un poco al micrófono.',
    'alto': 'Pico por encima de −6 dB: aléjate un poco del micrófono.',
    'ok': 'Nivel dentro de la guía.',
}


def nivel_toma(pico: float) -> str:
    """Estado del pico de la toma cruda frente a la guía (de -12 a -6 dB).

    >>> [nivel_toma(p) for p in (-80.0, -20.0, -9.0, -3.0)]
    ['silencio', 'bajo', 'ok', 'alto']
    """
    if pico <= SILENCIO_DB:
        return 'silencio'
    if pico < NIVEL_DB[0]:
        return 'bajo'
    if pico > NIVEL_DB[1]:
        return 'alto'
    return 'ok'
