"""Idiomas a los que se traducen los subtítulos (spec 021, D-4): datos, con el nombre de cada uno en su idioma."""

from __future__ import annotations

RECOMMENDED = 'en'
LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'pt': 'Português',
    'fr': 'Français',
    'it': 'Italiano',
    'de': 'Deutsch',
    'nl': 'Nederlands',
    'pl': 'Polski',
    'ja': '日本語',
    'ko': '한국어',
    'zh': '中文',
}


def name(code: str) -> str:
    """El nombre del idioma en su propio idioma; el código si no está en la lista."""
    return LANGUAGES.get(code, code)


def status() -> list[dict]:
    """La lista para el selector, con el ★ en el inglés."""
    return [{'code': code, 'name': label, 'recommended': code == RECOMMENDED} for code, label in LANGUAGES.items()]
