"""Servicios por tipo de trabajo: la API, el worker y el CLI usan los mismos (spec 004, D-2)."""

from content_studio.services import (
    music,
    music_samples,
    narration,
    narration_regenerate,
    storage_move,
    voice_build,
    voice_check,
)

SERVICES = {
    'narration': narration,
    'music': music,
    'music.samples': music_samples,
    'narration.regenerate': narration_regenerate,
    'voice.check': voice_check,
    'voice.build': voice_build,
    storage_move.KIND: storage_move,
}
