"""Los motores de música disponibles. Solo stdlib: lo leen el parser y el CLI sin cargar torch."""

from __future__ import annotations

from content_studio.music.motores.base import EspecMusica

_M = 'content_studio.music.motores.'
MODELOS: dict[str, EspecMusica] = {
    'acestep': EspecMusica(
        'acestep', '.venv-acestep', _M + 'acestep', 'AceStep', 'recomendado · ~30 s por pista', evalua=True
    ),
    'heartmula': EspecMusica('heartmula', '.venv-heartmula', _M + 'heartmula', 'HeartMuLa', 'lento · ~5 min por pista'),
}
