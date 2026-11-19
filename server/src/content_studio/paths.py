"""Rutas del checkout. Única fuente: los datos (venvs, motores, modelos y voces) viven en server/data/.

>>> NARRATION.parent.name, (ROOT / 'cli.py').is_file()
('data', True)
"""

from pathlib import Path

# server/src/content_studio/rutas.py → raíz del repo (solo desde el checkout)
ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / 'server'
SRC = SERVER / 'src'
DATA = SERVER / 'data'
OUT = ROOT / 'out'
LOGS = ROOT / 'logs'
DB = ROOT / 'var' / 'content-studio.db'  # base de la cola y las preferencias (spec 004, D-1); 009 y 015 la mueven
NARRATION = DATA / 'narration'
MUSIC = DATA / 'music'
REFERENCE = NARRATION / 'reference'
TAKES = REFERENCE / 'takes'
VOICES = NARRATION / 'voices'
