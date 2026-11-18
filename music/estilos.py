"""Shim temporal: el catálogo vive en src/content_studio/music/estilos.py (se borra al cerrar el refactor)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from content_studio.music.estilos import *  # noqa: E402, F403
