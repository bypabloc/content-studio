"""GET /music/styles: los presets de música con su categoría y si ya tienen muestra (spec 011, D-2 y D-3)."""

from __future__ import annotations

from fastapi import APIRouter

from content_studio import paths
from content_studio.music.styles import styles_catalog

router = APIRouter()


@router.get('/music/styles')
def music_styles() -> dict:
    """Catálogo de estilos para el buscador de la sección Música."""
    return {'styles': styles_catalog(paths.MUSIC / 'samples')}
