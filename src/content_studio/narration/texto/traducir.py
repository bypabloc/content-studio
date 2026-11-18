"""Texto que recibe cada motor: gestos, énfasis y signos que cada uno lee mal (§6.3)."""

from __future__ import annotations

import re

# Gestos y énfasis: van dentro del texto del bloque y traducir() los convierte según el motor (§6.3).
GESTO = re.compile(r'\[(risa|suspiro|respiro)\]', re.IGNORECASE)
ENFASIS = re.compile(r'\[enfasis\](.*?)\[/enfasis\]', re.IGNORECASE | re.DOTALL)
SUSPENSIVOS = re.compile(r'…(?=\s+\w)')  # "…" a mitad de oración: lo que sigue sigue la misma oración
# Cómo traduce cada motor las marcas del guion (§6.3). Un gesto que no está en `gestos` se quita con aviso;
# `puntos` y `raya` son reemplazos que cambian la lectura, así que también avisan.
TRADUCCION = {
    'omnivoice': dict(
        gestos={'risa': '[laughter]', 'suspiro': '[sigh]'}, enfasis='{}', puntos=',', raya=None, quitar='', digitos=None
    ),
    'voxcpm2': dict(gestos={}, enfasis='{}', puntos=None, raya=None, quitar='()*', digitos=None),
    'indextts': dict(
        gestos={},
        enfasis='{}',
        puntos=None,
        raya=',',
        quitar='',
        digitos='{motor} lee mal los dígitos; escríbelos en letras',
    ),
    'cosyvoice3': dict(
        gestos={'risa': '[laughter]', 'suspiro': '[sigh]', 'respiro': '[breath]'},
        enfasis='<strong>{}</strong>',
        puntos=None,
        raya=None,
        quitar='',
        digitos=None,
    ),
    # Qwen y Chatterbox: los gestos y el énfasis no se pueden pedir; los dígitos se leen mal (regla 13).
    'generico': dict(
        gestos={},
        enfasis='{}',
        puntos=None,
        raya=None,
        quitar='',
        digitos='{motor}: hay dígitos; escríbelos en letras (regla 13 de docs/formato-guion.md)',
    ),
}


def traducir(texto: str, motor: str) -> tuple[str, list[str]]:
    """Texto que recibe el motor a partir del texto de un bloque, y los avisos de lo que quitó o reemplazó (§6.3).

    >>> traducir('despacio… y no había nadie', 'omnivoice')
    ('despacio, y no había nadie', ['omnivoice: "…" a mitad de oración se cambió por ","'])
    >>> traducir('me dijo que sí [risa] no lo podía creer', 'omnivoice')
    ('me dijo que sí [laughter] no lo podía creer', [])
    >>> traducir('me dijo que sí [risa] no lo podía creer', 'qwen-0.6b')[1]
    ['qwen-0.6b no soporta [risa]; se quitó']
    >>> traducir('es [enfasis]gratis[/enfasis] para siempre', 'cosyvoice3')
    ('es <strong>gratis</strong> para siempre', [])
    >>> traducir('revisa el texto — y guarda', 'indextts')
    ('revisa el texto, y guarda', ['indextts: "—" se cambió por "," (lo lee "menos")'])
    >>> traducir('Hola (amigo) *hoy*', 'voxcpm2')
    ('Hola amigo hoy', ['voxcpm2 no soporta "()*"; se quitaron'])
    >>> traducir('son 3 piezas', 'indextts')
    ('son 3 piezas', ['indextts lee mal los dígitos; escríbelos en letras'])
    >>> traducir('me dijo que sí [suspiro] y se fue', 'omnivoice')[0]
    'me dijo que sí [sigh] y se fue'
    >>> traducir('ya casi [respiro] llego', 'cosyvoice3')[0]
    'ya casi [breath] llego'
    >>> traducir('me dijo que sí [risa] no lo podía creer', 'voxcpm2')
    ('me dijo que sí no lo podía creer', ['voxcpm2 no soporta [risa]; se quitó'])
    >>> traducir('Hola (amigo) *hoy*', 'cosyvoice3')[0]
    'Hola (amigo) *hoy*'
    >>> traducir('esto — aquello', 'chatterbox')
    ('esto — aquello', [])
    >>> traducir('pagó 3 veces', 'chatterbox')[1]
    ['chatterbox: hay dígitos; escríbelos en letras (regla 13 de docs/formato-guion.md)']
    >>> traducir('es [enfasis]gratis[/enfasis] para siempre', 'qwen-0.6b')[0]
    'es gratis para siempre'
    """
    cfg = TRADUCCION[motor if motor in TRADUCCION else 'generico']
    avisos: list[str] = []

    def gesto(m: re.Match) -> str:
        marca = m[1].lower()
        if marca in cfg['gestos']:
            return cfg['gestos'][marca]
        avisos.append(f'{motor} no soporta [{marca}]; se quitó')
        return ''

    texto = ENFASIS.sub(lambda m: cfg['enfasis'].format(m[1]), GESTO.sub(gesto, texto))
    if cfg['quitar'] and re.search(f'[{re.escape(cfg["quitar"])}]', texto):
        avisos.append(f'{motor} no soporta "{cfg["quitar"]}"; se quitaron')
        texto = re.sub(f'[{re.escape(cfg["quitar"])}]', '', texto)
    if cfg['puntos'] and SUSPENSIVOS.search(texto):
        avisos.append(f'{motor}: "…" a mitad de oración se cambió por "{cfg["puntos"]}"')
        texto = SUSPENSIVOS.sub(cfg['puntos'], texto)
    if cfg['raya'] and '—' in texto:
        avisos.append(f'{motor}: "—" se cambió por "{cfg["raya"]}" (lo lee "menos")')
        texto = texto.replace('—', cfg['raya'])
    if cfg['digitos'] and re.search(r'\d', texto):
        avisos.append(cfg['digitos'].format(motor=motor))
    texto = re.sub(r'\s+([,.;:!?])', r'\1', re.sub(r'\s{2,}', ' ', texto)).strip()
    return texto, avisos
