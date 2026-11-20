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
