"""GET /voices/catalog: las voces libres con su ficha, su estado y si son favoritas (spec 010, D-5, AC-7 y AC-9)."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from content_studio.api.deps import get_conn
from content_studio.db import settings as store
from content_studio.narration.styles import STYLES
from content_studio.narration.voices import catalog as voice_catalog

router = APIRouter()
FAVORITES = 'voices.favorites'  # lista de nombres de voz; la guarda PUT /settings/voices.favorites


@router.get('/voices/catalog')
def voices_catalog(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> dict:
    """Cada voz del catálogo con su ficha, su estado (no construida, parcial o aprobada) y sus estilos."""
    saved = store.get(conn, FAVORITES)
    favorites = saved if isinstance(saved, list) else []
    return {
        'voices': [
            {
                'id': name,
                'language': sheet.get('language'),
                'license': sheet.get('license'),
                'description': sheet.get('description'),
                'source': sheet.get('source'),
                'rights': sheet.get('rights'),
                'consent': sheet.get('consent'),
                'attribution': sheet.get('attribution'),
                'favorite': name in favorites,
                **voice_catalog.status(name, STYLES),
            }
            for name, sheet in voice_catalog.catalog().items()
        ]
    }
