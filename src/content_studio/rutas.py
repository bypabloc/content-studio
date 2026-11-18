"""Rutas del checkout. Única fuente: venvs, modelos y voces se quedan donde están (moverlos rompe los venvs).

>>> (RAIZ / 'cli.py').is_file() and SRC.name == 'src'
True
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]  # src/content_studio/rutas.py → raíz del repo (solo desde el checkout)
SRC = RAIZ / 'src'
OUT = RAIZ / 'out'
LOGS = RAIZ / 'logs'
NARRATION = RAIZ / 'narration'
MUSIC = RAIZ / 'music'
VOZ = NARRATION / 'voz'
TOMAS = VOZ / 'tomas'
VOCES = NARRATION / 'voces'
