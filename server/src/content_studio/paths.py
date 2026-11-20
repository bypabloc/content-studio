"""Rutas del checkout. Única fuente: los datos (venvs, motores, modelos y voces) viven en server/data/.

>>> NARRATION.parent.name, (SERVER / 'pyproject.toml').is_file()
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
DB = ROOT / 'var' / 'content-studio.db'  # base de la cola y las preferencias (spec 004, D-1); 010 y 020 la mueven
NARRATION = DATA / 'narration'
MUSIC = DATA / 'music'
REFERENCE = NARRATION / 'reference'
TAKES = REFERENCE / 'takes'
VOICES = NARRATION / 'voices'


def playable(path: Path) -> str | None:
    """Ruta de `path` desde la raíz del repo, la que pide /files; None si no existe o está fuera del repo.

    >>> playable(ROOT / 'server' / 'pyproject.toml')
    'server/pyproject.toml'
    >>> playable(ROOT / 'no-existe.wav') is None
    True
    """
    if not path.is_file():
        return None
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return None
