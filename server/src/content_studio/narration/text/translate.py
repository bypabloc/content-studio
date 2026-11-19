"""Texto que recibe cada motor: gestos, énfasis y signos que cada uno lee mal (§6.3)."""

from __future__ import annotations

import re

from content_studio.narration.text.segments import normalize

# Gestos y énfasis: van dentro del texto del bloque y translate() los convierte según el motor (§6.3).
GESTURE = re.compile(r'\[(laugh|sigh|breathing)\]', re.IGNORECASE)
EMPHASIS = re.compile(r'\[emphasis\](.*?)\[/emphasis\]', re.IGNORECASE | re.DOTALL)
SUSPENSIVE = re.compile(r'…(?=\s+\w)')  # "…" a mitad de oración: lo que sigue sigue la misma oración
# Cómo traduce cada motor las marcas del guion (§6.3). Un gesto que no está en `gestures` se quita con aviso;
# `points` y `raya` son reemplazos que cambian la lectura, así que también avisan.
TRANSLATION = {
    'omnivoice': dict(
        gestures={'laugh': '[laughter]', 'sigh': '[sigh]'}, emphasis='{}', points=',', raya=None, remove='', digits=None
    ),
    'voxcpm2': dict(gestures={}, emphasis='{}', points=None, raya=None, remove='()*', digits=None),
    'indextts': dict(
        gestures={},
        emphasis='{}',
        points=None,
        raya=',',
        remove='',
        digits='{engine} misreads digits; write them as words',
    ),
    'cosyvoice3': dict(
        gestures={'laugh': '[laughter]', 'sigh': '[sigh]', 'breathing': '[breath]'},
        emphasis='<strong>{}</strong>',
        points=None,
        raya=None,
        remove='',
        digits=None,
    ),
    # Qwen y Chatterbox: los gestos y el énfasis no se pueden pedir; los dígitos se leen mal (regla 13).
    'generic': dict(
        gestures={},
        emphasis='{}',
        points=None,
        raya=None,
        remove='',
        digits='{engine}: digits present; write them as words (rule 13 in docs/formato-guion.md)',
    ),
}


def translate(text: str, engine: str) -> tuple[str, list[str]]:
    """Texto que recibe el motor a partir del texto de un bloque, y los avisos de lo que quitó o reemplazó (§6.3).

    >>> translate('despacio… y no había nadie', 'omnivoice')
    ('despacio, y no había nadie', ['omnivoice: "…" mid-sentence changed to ","'])
    >>> translate('me dijo que sí [laugh] no lo podía creer', 'omnivoice')
    ('me dijo que sí [laughter] no lo podía creer', [])
    >>> translate('me dijo que sí [risa] no lo podía creer', 'qwen-0.6b')[1]
    ['qwen-0.6b does not support [laugh]; removed']
    >>> translate('es [enfasis]gratis[/enfasis] para siempre', 'cosyvoice3')
    ('es <strong>gratis</strong> para siempre', [])
    >>> translate('revisa el texto — y guarda', 'indextts')
    ('revisa el texto, y guarda', ['indextts: "—" changed to "," (the model reads it as "minus")'])
    >>> translate('Hola (amigo) *hoy*', 'voxcpm2')
    ('Hola amigo hoy', ['voxcpm2 does not support "()*"; removed'])
    >>> translate('son 3 piezas', 'indextts')
    ('son 3 piezas', ['indextts misreads digits; write them as words'])
    >>> translate('me dijo que sí [suspiro] y se fue', 'omnivoice')[0]
    'me dijo que sí [sigh] y se fue'
    >>> translate('ya casi [respiro] llego', 'cosyvoice3')[0]
    'ya casi [breath] llego'
    >>> translate('me dijo que sí [risa] no lo podía creer', 'voxcpm2')
    ('me dijo que sí no lo podía creer', ['voxcpm2 does not support [laugh]; removed'])
    >>> translate('Hola (amigo) *hoy*', 'cosyvoice3')[0]
    'Hola (amigo) *hoy*'
    >>> translate('esto — aquello', 'chatterbox')
    ('esto — aquello', [])
    >>> translate('pagó 3 veces', 'chatterbox')[1]
    ['chatterbox: digits present; write them as words (rule 13 in docs/formato-guion.md)']
    >>> translate('es [enfasis]gratis[/enfasis] para siempre', 'qwen-0.6b')[0]
    'es gratis para siempre'
    """
    cfg = TRANSLATION[engine if engine in TRANSLATION else 'generic']
    text = normalize(text)
    notices: list[str] = []

    def gesture(m: re.Match) -> str:
        mark = m[1].lower()
        if mark in cfg['gestures']:
            return cfg['gestures'][mark]
        notices.append(f'{engine} does not support [{mark}]; removed')
        return ''

    text = EMPHASIS.sub(lambda m: cfg['emphasis'].format(m[1]), GESTURE.sub(gesture, text))
    if cfg['remove'] and re.search(f'[{re.escape(cfg["remove"])}]', text):
        notices.append(f'{engine} does not support "{cfg["remove"]}"; removed')
        text = re.sub(f'[{re.escape(cfg["remove"])}]', '', text)
    if cfg['points'] and SUSPENSIVE.search(text):
        notices.append(f'{engine}: "…" mid-sentence changed to "{cfg["points"]}"')
        text = SUSPENSIVE.sub(cfg['points'], text)
    if cfg['raya'] and '—' in text:
        notices.append(f'{engine}: "—" changed to "{cfg["raya"]}" (the model reads it as "minus")')
        text = text.replace('—', cfg['raya'])
    if cfg['digits'] and re.search(r'\d', text):
        notices.append(cfg['digits'].format(engine=engine))
    text = re.sub(r'\s+([,.;:!?])', r'\1', re.sub(r'\s{2,}', ' ', text)).strip()
    return text, notices
