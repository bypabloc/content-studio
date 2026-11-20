"""Textos visibles del server: un catálogo por idioma en messages/ (spec 004, D-5; spec 007, D-1 a D-4)."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES = ('es', 'en', 'pt')
DEFAULT_LOCALE = 'es'
_DIR = Path(__file__).parent / 'messages'
_CATALOGS: dict[str, dict[str, str]] = {
    locale: json.loads((_DIR / f'{locale}.json').read_text(encoding='utf-8')) for locale in LOCALES
}


def negotiate(header: str | None) -> str:
    """Idioma soportado de una cabecera Accept-Language: el de mayor `q` (1 si no lo trae); sin ninguno, español.

    Un `q` mal formado o igual a 0 descarta ese idioma. Con el mismo `q`, gana el primero de la lista.
    """
    best, best_quality = DEFAULT_LOCALE, 0.0
    for item in (header or '').split(','):
        tag, _, parameters = item.partition(';')
        language = tag.strip().split('-')[0].lower()
        if language not in LOCALES:
            continue
        quality = _quality(parameters)
        if quality > best_quality:
            best, best_quality = language, quality
    return best


def _quality(parameters: str) -> float:
    """El `q` de los parámetros de un idioma; 1 si no lo trae y 0 si está mal formado."""
    for parameter in parameters.split(';'):
        name, _, value = parameter.partition('=')
        if name.strip() == 'q':
            try:
                return float(value)
            except ValueError:
                return 0.0
    return 1.0


def t(key: str, locale: str = DEFAULT_LOCALE, **params: object) -> str:
    """Texto de la clave en el idioma pedido, con sus parámetros. Sin catálogo para el idioma, usa español.

    Si falta un parámetro deja la plantilla; si falta la clave, la devuelve tal cual.
    """
    catalog = _CATALOGS.get(locale, _CATALOGS[DEFAULT_LOCALE])
    template = catalog.get(key, _CATALOGS[DEFAULT_LOCALE].get(key, key))
    try:
        return template.format(**params)
    except KeyError:
        return template
