"""POST /server/stop: el apagado que pide `studio api down` (spec 028, AC-6). Exige el token."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.post('/server/stop')
def stop(request: Request) -> dict[str, bool]:
    """Pide a `serve` que termine: cierra la API, borra api.json y suelta el lock."""
    if request.app.state.stop:
        request.app.state.stop()
    return {'stopping': True}
