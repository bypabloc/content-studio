"""Corte del guion en bloques: oraciones de hasta MAX_CHARS, pausas, [estilo:] y [emocion:] (§5.1).
Ver server/data/narration/docs/formato-guion.md."""

from __future__ import annotations

import re

MAX_CHARS = 300
PAUSA_SEG = 0.25
PAUSA_PARRAFO = 0.6
# Marcas que cortan el texto en bloques: [pausa N] (grupo 1), [estilo: nombre] (2),
# [emocion: nombre 0.4] (3 y 4) y la línea en blanco. El modelo no las ve.
MARCA_BLOQUE = re.compile(
    r'\[pausa\s+(\d+(?:[.,]\d+)?)\s*s?\]'
    r'|\[estilo:\s*([\w-]*)\s*\]'
    r'|\[emocion:\s*(\w*)\s*(\d+(?:[.,]\d+)?)?\s*\]'
    r'|\n[ \t]*\n',
    re.IGNORECASE,
)
# Todas las marcas de la gramática, para quitarlas antes de comparar o de buscar etiquetas ajenas.
SIN_MARCAS = re.compile(
    r'\[pausa\s+[\d.,]+\s*s?\]|\[estilo:[^\]]*\]|\[emocion:[^\]]*\]'
    r'|\[(?:risa|suspiro|respiro)\]|\[/?enfasis\]|\n[ \t]*\n',
    re.IGNORECASE,
)
# Qwen Base lee estas marcas en voz alta ("[breath]" sonó "Braids"). Ver docs/formato-guion.md.
ETIQUETA = re.compile(r'\[[^\]]*\]|<[^>]*>|\*\*|\(pausa\)', re.IGNORECASE)


def trozos(texto: str) -> list[str]:
    """Agrupa oraciones en bloques de hasta MAX_CHARS.

    >>> trozos('Hola. ' * 3)
    ['Hola. Hola. Hola.']
    >>> len(trozos('a' * 200 + '. ' + 'b' * 200 + '.'))
    2
    """
    out: list[str] = []
    for oracion in re.split(r'(?<=[.!?…])\s+', ' '.join(texto.split())):
        if out and len(out[-1]) + len(oracion) < MAX_CHARS:
            out[-1] += ' ' + oracion
        elif oracion:
            out.append(oracion)
    return out


def segmentos(texto: str, estilo: str = 'experta') -> list[dict]:
    """Bloques a generar, cada uno con su silencio final, su estilo y su emoción (§5.1).

    Una línea en blanco deja PAUSA_PARRAFO. [pausa N] deja N segundos: si hay alguna entre dos bloques,
    mandan esas marcas (se suman) y no las líneas en blanco. [estilo:] y [emocion:] cortan el bloque: el
    cambio rige desde ese punto hasta el próximo de su tipo. Un corte a mitad de oración deja un aviso.

    >>> [(b['texto'], b['pausa']) for b in segmentos('Hola. Chao.')]
    [('Hola. Chao.', 0.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno.\\n\\nDos.')]
    [('Uno.', 0.6), ('Dos.', 0.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno. [pausa 1,5] Dos. [PAUSA 2s]')]
    [('Uno.', 1.5), ('Dos.', 2.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno.\\n\\n[pausa 0.2]\\n\\nDos.')]
    [('Uno.', 0.2), ('Dos.', 0.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno.\\n \\n[pausa 1] [pausa 2]\\nDos.')]
    [('Uno.', 3.0), ('Dos.', 0.0)]
    >>> [b['pausa'] for b in segmentos('a' * 200 + '. ' + 'b' * 200 + '.')]
    [0.25, 0.0]
    >>> segmentos('[pausa 1]\\n\\n')
    []
    >>> [(b['texto'], b['estilo'], b['emocion'])
    ...  for b in segmentos('Uno. [estilo: dramatica] Dos. [emocion: miedo 0.4] Tres.')]
    [('Uno.', 'experta', None), ('Dos.', 'dramatica', None), ('Tres.', 'dramatica', ('miedo', 0.4))]
    >>> [(b['texto'], b['estilo']) for b in segmentos('Uno.', 'suave')]
    [('Uno.', 'suave')]
    >>> [b['avisos'] for b in segmentos('Hola, [estilo: intima] adiós.')]
    [['cambio de estilo a mitad de oración'], []]
    >>> [(b['texto'], b['emocion']) for b in segmentos('Uno.\\n\\n[emocion: triste]Dos. [emocion:]Tres.')]
    [('Uno.', None), ('Dos.', ('triste', 0.6)), ('Tres.', None)]
    """
    out: list[dict] = []
    marcas, hay_marca, blanco, pos = 0.0, False, False, 0
    actual, emo = estilo, None
    for m in [*MARCA_BLOQUE.finditer(texto), None]:
        fin = m.start() if m else len(texto)
        previo = texto[pos:fin]
        for t in trozos(previo):
            if out:
                out[-1]['pausa'] = marcas if hay_marca else PAUSA_PARRAFO if blanco else PAUSA_SEG
            out.append(dict(texto=t, pausa=0.0, estilo=actual, emocion=emo, avisos=[]))
            marcas, hay_marca, blanco = 0.0, False, False
        if m is None:
            break
        if m[1]:
            marcas, hay_marca = marcas + float(m[1].replace(',', '.')), True
        elif m[2] is not None or m[3] is not None:
            if out and previo.strip() and not re.search(r'[.!?…:]\s*$', previo):
                out[-1]['avisos'].append(f'cambio de {"estilo" if m[2] is not None else "emoción"} a mitad de oración')
            if m[2] is not None:
                actual = m[2]
            else:
                emo = (m[3].lower(), float(m[4].replace(',', '.')) if m[4] else 0.6) if m[3] else None
        else:
            blanco = True
        pos = m.end()
    if out and hay_marca:
        out[-1]['pausa'] = marcas
    return out


def etiquetas(texto: str) -> list[str]:
    """Marcas que el modelo pronunciaría. Las de la gramática (pausa, estilo, emoción, gestos, énfasis) no cuentan.

    >>> etiquetas('Hola [breath] <break time="1s"/> **ojo** (pausa) [pausa 1]')
    ['[breath]', '<break time="1s"/>', '**', '(pausa)']
    >>> etiquetas('Texto limpio, con pausa.\\n\\nY otro párrafo.')
    []
    >>> etiquetas('[risa] [estilo: dramatica] [emocion: triste 0.4] [enfasis]sí[/enfasis] [respiro]')
    []
    """
    return list(dict.fromkeys(ETIQUETA.findall(SIN_MARCAS.sub(' ', texto))))
