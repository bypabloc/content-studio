"""Kit de grabación de las referencias propias (spec 010, D-6): orden, duración, ppm y guion de cada estilo.

Los datos salen de docs/scripts/README.md. Cada guion (`docs/scripts/<n>-<estilo>.md`) trae la versión marcada, con la
notación del teleprompter, y el texto exacto: el que se graba y se guarda como transcripción.
"""

from __future__ import annotations

from pathlib import Path

from content_studio import paths

# cspell:ignore amistosa experta estable energica dramatica: nombres de los guiones en docs/scripts/.
# Estilo, duración (s), ppm de la guía (None si no tiene ritmo fijo) y guion. La neutral abre y cierra la sesión.
KIT = [
    ('neutral', 10, 12, 150, '00-neutral.md'),
    ('friendly', 9, 11, 165, '01-amistosa.md'),
    ('expert', 10, 12, 150, '03-experta.md'),
    ('clear', 10, 12, 140, '04-clara.md'),
    ('steady', 10, 11, 160, '05-estable.md'),
    ('soft', 10, 11, 140, '02-suave.md'),
    ('energetic', 8, 10, 175, '06-energica.md'),
    ('dramatic', 10, 12, 130, '07-dramatica.md'),
    ('sad', 10, 12, 120, '08-triste.md'),
    ('intimate', 9, 11, 125, '09-intima.md'),
    ('neutral-en', 10, 12, 150, '10-neutral-en.md'),
    ('neutral-end', 10, 12, 150, '00-neutral.md'),  # segunda neutral para cerrar: mismo texto que la primera
]
# Opcional y al final: solo para efectos; pierde timbre (09-intima.md, variante susurro).
OPTIONAL = [('whisper', 7, 9, None, '09-intima.md')]
STYLES = [row[0] for row in KIT + OPTIONAL]
SCRIPTS = paths.NARRATION / 'docs' / 'scripts'


def kit() -> list[dict]:
    """Los estilos en orden de sesión: los obligatorios y, al final, el opcional."""
    return [
        {'style': style, 'duration': (low, high), 'ppm': ppm, 'optional': optional, 'script': script}
        for rows, optional in ((KIT, False), (OPTIONAL, True))
        for style, low, high, ppm, script in rows
    ]


def _row(style: str) -> tuple:
    """La fila del estilo en el kit; ValueError si no es un estilo del kit."""
    for row in KIT + OPTIONAL:
        if row[0] == style:
            return row
    raise ValueError(f'not a kit style: {style!r}')


def script_file(style: str) -> Path:
    """El guion del estilo en docs/scripts/."""
    return SCRIPTS / _row(style)[4]


def _section(text: str, heading: str) -> list[str]:
    """Las líneas de una sección `## ...` del guion, sin el encabezado."""
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith('## '):
            inside = line.startswith(heading)
        elif inside:
            lines.append(line)
    return lines


def marked_text(style: str) -> str:
    """La versión marcada del guion, con su notación: es lo que muestra el teleprompter."""
    lines = _section(script_file(style).read_text(encoding='utf-8'), '## Versión marcada')
    return '\n'.join(line[1:].strip() for line in lines if line.startswith('>'))


def plain_text(style: str) -> str:
    """El texto exacto del guion, sin marcas: el que se graba y se guarda como transcripción."""
    lines = _section(script_file(style).read_text(encoding='utf-8'), '## Texto exacto')
    return ' '.join(line.strip() for line in lines if line.strip() and not line.strip().startswith('```'))
