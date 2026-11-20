"""Voces propias (spec 010, D-1 y D-3): perfiles, tomas, elegir una y el kit de grabación."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from content_studio.api.deps import get_conn
from content_studio.api.errors import ApiError
from content_studio.jobs import queue
from content_studio.narration import profile_takes, profiles, recording_kit

router = APIRouter()


class Name(BaseModel):
    """Nombre visible de un perfil."""

    name: str = Field(min_length=1, max_length=80)


def _profile(slug: str) -> None:
    """404 si el perfil no existe."""
    if not profiles.exists(slug):
        raise ApiError(404, 'unknown_profile', profile=slug)


def _style(style: str) -> None:
    """422 si el estilo no es del kit."""
    if style not in recording_kit.STYLES:
        raise ApiError(422, 'unknown_style', style=style)


def _kit_item(item: dict) -> dict:
    """Un estilo del kit para la pantalla: duración como mínimo y máximo, ppm, texto exacto y versión marcada."""
    low, high = item['duration']
    return {
        'style': item['style'],
        'duration': {'min': low, 'max': high},
        'ppm': item['ppm'],
        'optional': item['optional'],
        'text': recording_kit.plain_text(item['style']),
        'marked': recording_kit.marked_text(item['style']),
    }


@router.get('/voices/kit')
def kit() -> dict:
    """Los estilos de grabación en orden de sesión, con su duración, ppm, guion y texto exacto."""
    return {'styles': [_kit_item(item) for item in recording_kit.kit()]}


@router.get('/voices/profiles')
def list_profiles() -> list[dict]:
    """Los perfiles con los estilos que ya tienen."""
    return profiles.list_profiles()


@router.post('/voices/profiles', status_code=201)
def create_profile(body: Name) -> dict:
    """Crea un perfil. 409 si ya existe; 422 si el nombre no tiene letras ni números."""
    try:
        slug = profiles.create(body.name)
    except profiles.ProfileExists:
        raise ApiError(409, 'profile_exists', profile=profiles.slugify(body.name)) from None
    except ValueError:
        raise ApiError(422, 'invalid_profile_name') from None
    return {'id': slug, 'name': body.name}


@router.get('/voices/profiles/{slug}')
def get_profile(slug: str) -> dict:
    """Un perfil con cada estilo del kit: si tiene referencia elegida y cuántas tomas."""
    _profile(slug)
    return {'id': slug, 'name': profiles.name_of(slug), 'styles': profiles.styles_status(slug)}


@router.patch('/voices/profiles/{slug}')
def rename_profile(slug: str, body: Name) -> dict:
    """Cambia el nombre visible; la carpeta y las referencias no cambian."""
    _profile(slug)
    profiles.rename(slug, body.name)
    return {'id': slug, 'name': body.name}


@router.delete('/voices/profiles/{slug}', status_code=204)
def delete_profile(slug: str, confirm: bool = False) -> Response:
    """Borra un perfil vacío. Con archivos hace falta `confirm=true`, y entonces va a la papelera."""
    _profile(slug)
    try:
        profiles.delete(slug, confirm=confirm)
    except profiles.ProfileNotEmpty:
        raise ApiError(409, 'profile_not_empty', profile=slug) from None
    return Response(status_code=204)


@router.post('/voices/profiles/{slug}/takes/{style}', status_code=201)
async def add_take(
    slug: str, style: str, request: Request, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> dict:
    """Guarda el WAV del cuerpo como la siguiente toma del estilo y encola su chequeo (`voice.check`)."""
    _profile(slug)
    _style(style)
    take = profile_takes.save_take(slug, style, await request.body())
    params = {'profile': slug, 'style': style, 'take': take}
    job = queue.enqueue(conn, 'voice.check', params, request.app.state.services)
    return {'style': style, 'take': take, 'job': job}


@router.get('/voices/profiles/{slug}/takes/{style}')
def list_takes(slug: str, style: str) -> dict:
    """Números de las tomas del estilo."""
    _profile(slug)
    _style(style)
    return {'style': style, 'takes': profile_takes.list_takes(slug, style)}


@router.post('/voices/profiles/{slug}/takes/{style}/{take}/choose')
def choose_take(slug: str, style: str, take: int) -> dict:
    """Hace de la toma la referencia del estilo; la referencia anterior pasa a las tomas."""
    _profile(slug)
    _style(style)
    try:
        profile_takes.choose(slug, style, take)
    except profile_takes.TakeNotFound:
        raise ApiError(404, 'take_not_found', take=take) from None
    return {'style': style, 'take': take}
