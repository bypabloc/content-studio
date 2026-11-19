"""Renombres de los datos de narración a inglés (spec 002, D-4): lo que aplica el paso 2 de `move-data`.

`nuevo(rel)` dice cómo se llama ahora una ruta de `server/data/narration/` (relativa, con `/`). Es idempotente: una ruta
ya renombrada no cambia, así que una segunda corrida no hace nada. Las emociones no tienen archivos: su tabla va en la
ficha de WARNING y el código las renombra a mano.

>>> nuevo('voz/experta.wav'), nuevo('voz/tomas/toma1.wav'), nuevo('voces/catalogo.json')
('reference/expert.wav', 'reference/takes/toma1.wav', 'voices/catalog.json')
>>> nuevo('reference/expert.wav'), nuevo('docs/guiones/guion.txt'), nuevo('motores/index-tts/a.pth')
('reference/expert.wav', 'docs/scripts/guion.txt', 'engines/index-tts/a.pth')
"""

from __future__ import annotations

# Estilos de narración: la referencia `reference/<estilo>.wav|.txt` toma el nombre nuevo (D-4).
ESTILOS = {
    'amistosa': 'friendly',
    'suave': 'soft',
    'experta': 'expert',
    'clara': 'clear',
    'estable': 'steady',
    'neutral': 'neutral',
    'energica': 'energetic',
    'dramatica': 'dramatic',
    'triste': 'sad',
    'intima': 'intimate',
    'susurro': 'whisper',
    'neutral-en': 'neutral-en',
    'neutral-fin': 'neutral-end',
}
# Carpetas (viejo, nuevo): la más larga primero, porque `voz/tomas` vive dentro de `voz`.
CARPETAS = (
    ('voz/tomas', 'reference/takes'),
    ('voz', 'reference'),
    ('voces', 'voices'),
    ('motores', 'engines'),
    ('docs/guiones', 'docs/scripts'),
)
ARCHIVOS = {'voices/catalogo.json': 'voices/catalog.json'}


def nuevo(rel: str) -> str:
    for viejo, nueva in CARPETAS:
        if rel == viejo or rel.startswith(viejo + '/'):
            rel = nueva + rel[len(viejo) :]
            break
    rel = ARCHIVOS.get(rel, rel)
    carpeta, _, nombre = rel.rpartition('/')
    stem, _, ext = nombre.rpartition('.')
    if carpeta == 'reference' and ext in ('wav', 'txt') and stem in ESTILOS:
        return f'{carpeta}/{ESTILOS[stem]}.{ext}'
    return rel
