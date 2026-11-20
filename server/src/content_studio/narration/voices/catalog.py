"""Catálogo de voces libres y su estado de aprobación. Solo stdlib: lo leen el parser de tts y el CLI."""

from __future__ import annotations

import json
from collections.abc import Collection

from content_studio.paths import VOICES

CATALOG = VOICES / 'catalog.json'


def catalog() -> dict:
    """Catálogo de voces libres (JSON)."""
    return json.loads(CATALOG.read_text(encoding='utf-8'))


def approved_voices(styles: Collection[str]) -> dict[str, dict]:
    """Voces del catálogo construidas y aprobadas en todos los `estilos`: {nombre: ficha del catálogo}."""
    out = {}
    for name, sheet in catalog().items():
        # cspell:ignore aprobacion
        # aprobacion.json: nombre en disco de las voces construidas (move-data no lo cambia, ver WARNING 002).
        # Claves en inglés desde la migración (WARNING 002-voces-migracion).
        ap = VOICES / name / 'aprobacion.json'
        if not ap.exists():
            continue
        res = json.loads(ap.read_text(encoding='utf-8'))['styles']
        if all(res.get(e, {}).get('ok') and (VOICES / name / f'{e}.wav').exists() for e in styles):
            out[name] = sheet
    return out


def mention(sheet: dict) -> str | None:
    """Texto de crédito que hay que publicar con la narración (descripción del video), o None si la licencia no lo pide.

    >>> mention({'license': 'CC0'}) is None
    True
    >>> mention({'license': 'CC BY 4.0', 'attribution': 'Voz: X, CC BY 4.0'})
    'Voz: X, CC BY 4.0'
    """
    return sheet.get('attribution')


def state(name: str, styles: Collection[str]) -> str:
    """Texto corto para listados y selectores: aprobada, reprobada (cuántos estilos) o sin construir.

    >>> state('no-existe', ['neutral'])
    'not built'
    """
    ap = VOICES / name / 'aprobacion.json'
    if not ap.exists():
        return 'not built'
    res = json.loads(ap.read_text(encoding='utf-8'))['styles']
    bad = [e for e in styles if not res.get(e, {}).get('ok')]
    return 'approved' if not bad else f'rejected in {len(bad)}/{len(styles)} styles ({", ".join(bad)})'


def status(name: str, styles: Collection[str]) -> dict:
    """Estado de una voz para la API: `not_built`, `partial` o `approved`, y si cada estilo está aprobado.

    >>> status('no-existe', ['neutral'])['state']
    'not_built'
    """
    ap = VOICES / name / 'aprobacion.json'  # cspell:ignore aprobacion
    if not ap.exists():
        return {'state': 'not_built', 'styles': [{'style': e, 'approved': False} for e in styles]}
    res = json.loads(ap.read_text(encoding='utf-8'))['styles']
    approved = {e: bool(res.get(e, {}).get('ok') and (VOICES / name / f'{e}.wav').exists()) for e in styles}
    state = 'approved' if all(approved.values()) else 'partial'
    return {'state': state, 'styles': [{'style': e, 'approved': ok} for e, ok in approved.items()]}
