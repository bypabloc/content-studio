"""Los motores de música disponibles. Solo stdlib: lo leen el parser y el CLI sin cargar torch."""

from __future__ import annotations

from content_studio.music.engines.base import MusicSpec

_M = 'content_studio.music.engines.'
MODELS: dict[str, MusicSpec] = {
    'acestep': MusicSpec(
        'acestep', '.venv-acestep', _M + 'acestep', 'AceStep', 'recommended · ~30 s per track', evaluates=True
    ),
    'heartmula': MusicSpec('heartmula', '.venv-heartmula', _M + 'heartmula', 'HeartMuLa', 'slow · ~5 min per track'),
}
