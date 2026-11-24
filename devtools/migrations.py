"""Renombres de los datos de narración (spec 002, D-4: paso 2 de `move-data`) y el perfil default (spec 010: paso 3).

`nuevo(rel)` dice cómo se llama ahora una ruta de `server/data/narration/` (relativa, con `/`). Es idempotente: una ruta
ya renombrada no cambia, así que una segunda corrida no hace nada. Las emociones no tienen archivos: su tabla va en la
ficha de WARNING y el código las renombra a mano.

>>> new('voz/experta.wav'), new('voz/tomas/toma1.wav'), new('voces/catalogo.json')
('reference/expert.wav', 'reference/takes/toma1.wav', 'voices/catalog.json')
>>> new('reference/expert.wav'), new('docs/guiones/guion.txt'), new('motores/index-tts/a.pth')
('reference/expert.wav', 'docs/scripts/guion.txt', 'engines/index-tts/a.pth')
>>> profile_path('reference/expert.wav'), profile_path('reference/takes/expert/2.wav')
('reference/default/expert.wav', 'reference/default/takes/expert/2.wav')
"""

from __future__ import annotations

# Estilos de narración: la referencia `reference/<estilo>.wav|.txt` toma el nombre nuevo (D-4).
STYLES = {
    # cspell:ignore amistosa experta estable energica dramatica susurro motores catalogo
    # (nombres viejos de los datos, D-4: son lo que la migración busca en disco).
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
FOLDERS = (
    ('voz/tomas', 'reference/takes'),
    ('voz', 'reference'),
    ('voces', 'voices'),
    ('motores', 'engines'),
    ('docs/guiones', 'docs/scripts'),
)
FILES = {'voices/catalogo.json': 'voices/catalog.json'}


def new(rel: str) -> str:
    """Ruta nueva de un archivo renombrado a inglés, según FOLDERS."""
    for old, new in FOLDERS:
        if rel == old or rel.startswith(old + '/'):
            rel = new + rel[len(old) :]
            break
    rel = FILES.get(rel, rel)
    folder, _, name = rel.rpartition('/')
    stem, _, ext = name.rpartition('.')
    if folder == 'reference' and ext in ('wav', 'txt') and stem in STYLES:
        return f'{folder}/{STYLES[stem]}.{ext}'
    return rel


# cspell:ignore perfil
# Paso 3 (spec 010, D-1): referencias sueltas, tomas, emociones y pruebas van al perfil default.
PROFILE = 'reference/default'
PROFILE_FOLDERS = ('reference/takes/', 'reference/emotions/', 'reference/test/')


def profile_path(rel: str) -> str:
    """Ruta dentro del perfil default (paso 3). Idempotente: lo que ya está en reference/default/ no cambia."""
    top_file = rel.startswith('reference/') and rel.count('/') == 1 and rel.rpartition('.')[2] in ('wav', 'txt')
    if top_file or rel.startswith(PROFILE_FOLDERS):
        return PROFILE + rel[len('reference') :]
    return rel
