"""Catálogo de voces libres y su estado de aprobación. Solo stdlib: lo leen el parser de tts y el CLI."""

from __future__ import annotations

import json

from content_studio.rutas import VOCES

CATALOGO = VOCES / 'catalogo.json'


def catalogo() -> dict:
    return json.loads(CATALOGO.read_text(encoding='utf-8'))


def aprobadas(estilos) -> dict[str, dict]:
    """Voces del catálogo construidas y aprobadas en todos los `estilos`: {nombre: ficha del catálogo}."""
    out = {}
    for nombre, ficha in catalogo().items():
        ap = VOCES / nombre / 'aprobacion.json'
        if not ap.exists():
            continue
        res = json.loads(ap.read_text(encoding='utf-8'))['estilos']
        if all(res.get(e, {}).get('ok') and (VOCES / nombre / f'{e}.wav').exists() for e in estilos):
            out[nombre] = ficha
    return out


def mencion(ficha: dict) -> str | None:
    """Texto de crédito que hay que publicar con la narración (descripción del video), o None si la licencia no lo pide.

    >>> mencion({'licencia': 'CC0'}) is None
    True
    >>> mencion({'licencia': 'CC BY 4.0', 'atribucion': 'Voz: X, CC BY 4.0'})
    'Voz: X, CC BY 4.0'
    """
    return ficha.get('atribucion')


def estado(nombre: str, estilos) -> str:
    """Texto corto para menús: aprobada, reprobada (cuántos estilos) o sin construir.

    >>> estado('no-existe', ['neutral'])
    'sin construir'
    """
    ap = VOCES / nombre / 'aprobacion.json'
    if not ap.exists():
        return 'sin construir'
    res = json.loads(ap.read_text(encoding='utf-8'))['estilos']
    malos = [e for e in estilos if not res.get(e, {}).get('ok')]
    return 'aprobada' if not malos else f'reprobada en {len(malos)}/{len(estilos)} estilos ({", ".join(malos)})'
