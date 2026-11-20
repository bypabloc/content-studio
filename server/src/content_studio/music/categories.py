"""Categorías de los presets (spec 011, D-2): de su nombre sale la familia que ve la UI. Solo stdlib."""

from __future__ import annotations

CATEGORIES = (
    'lofi',
    'ads',
    'demo',
    'corporate',
    'ambient',
    'cinematic',
    'tutorial',
    'documentary',
    'acoustic',
    'electronic',
    'jazz',
    'wellness',
    'genres',
)

# Cada familia con los primeros segmentos de nombre que la forman (lofi-jazz → lofi). Lo que no encaja, en OVERRIDES.
FAMILIES = {
    'lofi': ('lofi', 'chillhop'),
    'ads': ('ad',),
    'demo': ('demo', 'casual', 'kids', 'vlog', 'cooking'),
    'corporate': ('corporate', 'news'),
    'ambient': ('ambient', 'new'),
    'cinematic': ('cinematic', 'sci', 'trailer', 'heroic', 'mystery', 'suspense', 'fantasy'),
    'tutorial': ('tutorial', 'course', 'step', 'code', 'explainer'),
    'documentary': ('documentary',),
    'acoustic': ('acoustic', 'piano', 'folk', 'country', 'ukulele', 'guitar', 'harp', 'celtic'),
    'jazz': ('jazz', 'bossa', 'lounge', 'swing'),
    'wellness': ('meditation', 'yoga', 'spa', 'sleep'),
    'electronic': (
        'future',
        'deep',
        'tech',
        'techno',
        'house',
        'drum',
        'edm',
        'electropop',
        'downtempo',
        'chillwave',
        'vaporwave',
        'synthwave',
        'retrowave',
        'chiptune',
        'workout',
    ),
}
BY_PREFIX = {prefix: family for family, prefixes in FAMILIES.items() for prefix in prefixes}
# Lo que el prefijo no dice bien: el nombre completo gana sobre su familia.
OVERRIDES = {
    'deep-focus': 'ambient',
    'tropical-house': 'electronic',
}


def category_of(name: str) -> str:
    """La categoría de un preset: su excepción, su familia por el prefijo, o `genres` si no tiene una.

    >>> category_of('lofi-jazz'), category_of('deep-focus'), category_of('pop-song')
    ('lofi', 'ambient', 'genres')
    """
    if name in OVERRIDES:
        return OVERRIDES[name]
    return BY_PREFIX.get(name.split('-')[0], 'genres')
