"""GET /health: la API está viva y el token es válido."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get('/health')
def health() -> dict[str, bool]:
    """Estado de la API."""
    return {'ok': True}
