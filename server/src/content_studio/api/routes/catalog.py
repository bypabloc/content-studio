"""GET /catalog/{kind}: motores, estilos y voces, con `recommended` y si el motor está instalado (spec 004, D-5)."""

from __future__ import annotations

from fastapi import APIRouter

from content_studio.api.errors import ApiError
from content_studio.music.engines.registry import MODELS
from content_studio.music.styles import STYLES as MUSIC_STYLES
from content_studio.narration import profiles
from content_studio.narration.parser import ENGINES, STYLES, approved_voices

router = APIRouter()
# La misma opción por defecto que el parser del CLI: es la que lleva ★ en cada selector de estilo.
DEFAULT_STYLE = {'narration': 'expert', 'music': 'lofi-chill'}


@router.get('/catalog/{kind}')
def catalog(kind: str) -> dict:
    """Catálogo de un tipo de trabajo. Cada selector trae exactamente una opción `recommended`."""
    if kind == 'narration':
        return {
            'engines': [
                {
                    'id': spec.name,
                    'license': spec.license,
                    'commercial': spec.commercial,
                    'installed': spec.installed(),
                    'recommended': spec.recommended,
                    'note': spec.note,
                    'batch': spec.batch,
                }
                for spec in ENGINES.values()
            ],
            'styles': [{'id': name, 'recommended': name == DEFAULT_STYLE[kind]} for name in STYLES],
            'voices': [{'id': name, 'language': sheet['language']} for name, sheet in approved_voices(STYLES).items()],
            'profiles': profiles.list_profiles(),
        }
    if kind == 'music':
        return {
            'models': [
                {
                    'id': spec.name,
                    'desc': spec.desc,
                    'installed': spec.installed(),
                    'recommended': spec.recommended,
                    'evaluates': spec.evaluates,
                }
                for spec in MODELS.values()
            ],
            'styles': [
                {
                    'id': name,
                    'key': style.get('key'),
                    'bpm': style.get('bpm'),
                    'recommended': name == DEFAULT_STYLE[kind],
                }
                for name, style in MUSIC_STYLES.items()
            ],
        }
    raise ApiError(404, 'not_found')
