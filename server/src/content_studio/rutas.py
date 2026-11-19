"""Rutas del checkout. Única fuente: los datos (venvs, motores, modelos y voces) viven en server/data/.

>>> NARRATION.parent.name, (RAIZ / 'cli.py').is_file()
('data', True)
"""

from pathlib import Path

# server/src/content_studio/rutas.py → raíz del repo (solo desde el checkout)
RAIZ = Path(__file__).resolve().parents[3]
SERVER = RAIZ / 'server'
SRC = SERVER / 'src'
DATA = SERVER / 'data'
OUT = RAIZ / 'out'
LOGS = RAIZ / 'logs'
NARRATION = DATA / 'narration'
MUSIC = DATA / 'music'
VOZ = NARRATION / 'voz'
TOMAS = VOZ / 'tomas'
VOCES = NARRATION / 'voces'
