"""Rutas del checkout y del almacenamiento elegido.

>>> (SERVER / 'pyproject.toml').is_file()
True
"""

import os
import sqlite3
from contextlib import closing
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / 'server'
SRC = SERVER / 'src'
DATA = SERVER / 'data'
LOGS = ROOT / 'logs'
NARRATION = DATA / 'narration'
MUSIC = DATA / 'music'
REFERENCE = NARRATION / 'reference'
TAKES = REFERENCE / 'takes'
VOICES = NARRATION / 'voices'


def data_dir() -> Path:
    """Carpeta de datos de usuario. CONTENT_STUDIO_HOME permite aislar una instalación."""
    override = os.environ.get('CONTENT_STUDIO_HOME')
    if override:
        return Path(override).expanduser().resolve()
    if os.name == 'nt':
        # cspell:ignore LOCALAPPDATA
        local = os.environ.get('LOCALAPPDATA')
        return (Path(local) if local else Path.home() / 'AppData' / 'Local') / 'Content Studio'
    return Path.home() / '.local' / 'share' / 'content-studio'


def db_path() -> Path:
    """Base de preferencias y trabajos, independiente de los settings de almacenamiento."""
    override = os.environ.get('CONTENT_STUDIO_DB')
    if override:
        return Path(override).expanduser().resolve()
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed':
        return data_dir() / 'content-studio.db'
    return ROOT / 'var' / 'content-studio.db'


def _mtime(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


@lru_cache(maxsize=8)
def _storage(database: Path, revision: tuple[int, int]) -> tuple[object, object]:
    """Lee las dos preferencias en una instantánea; la revisión incluye el WAL de SQLite."""
    if not revision[0]:
        return None, None
    with closing(sqlite3.connect(f'{database.resolve().as_uri()}?mode=ro', uri=True)) as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'settings'").fetchone():
            return None, None
        from content_studio.db import settings

        return settings.get(conn, 'storage.engines'), settings.get(conn, 'storage.outputs')


def _storage_paths(database: Path | None) -> tuple[object, object]:
    database = database if database is not None else db_path()
    if database == Path(':memory:'):
        return None, None
    return _storage(database, (_mtime(database), _mtime(database.with_name(database.name + '-wal'))))


def engines_dir(database: Path | None = None) -> Path:
    """Raíz de venvs y pesos administrados por la app."""
    configured, _ = _storage_paths(database)
    if isinstance(configured, str) and configured:
        return Path(configured).expanduser().resolve()
    return data_dir() / 'engines'


def models_cache() -> Path:
    """Caché compartida de modelos de Hugging Face administrados por la app."""
    return engines_dir() / 'hf'


def engine_root(kind: str, venv: str) -> Path:
    """Usa la instalación administrada o conserva el venv externo del checkout en desarrollo."""
    managed = engines_dir() / kind
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed' or (managed / venv).is_dir():
        return managed
    return NARRATION if kind == 'narration' else MUSIC


def references_dir() -> Path:
    """Perfiles del checkout en desarrollo y del usuario en el modo instalado."""
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed':
        return data_dir() / 'narration' / 'reference'
    return REFERENCE


def voices_dir() -> Path:
    """Voces construidas por el usuario. El catálogo versionado vive por separado."""
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed':
        return data_dir() / 'narration' / 'voices'
    return VOICES


def samples_dir() -> Path:
    """Muestras musicales del checkout en desarrollo y del usuario en la app instalada."""
    base = data_dir() / 'music' if os.environ.get('CONTENT_STUDIO_MODE') == 'installed' else MUSIC
    return base / 'samples'


def outputs_dir(database: Path | None = None) -> Path:
    """Carpeta de resultados, en Documentos si la app está instalada."""
    _, configured = _storage_paths(database)
    if isinstance(configured, str) and configured:
        return Path(configured).expanduser().resolve()
    if os.environ.get('CONTENT_STUDIO_MODE') == 'installed':
        return Path.home() / 'Documents' / 'Content Studio'
    return ROOT / 'out'


def playable(path: Path) -> str | None:
    """Ruta para /files, relativa al checkout cuando es posible y absoluta en el almacenamiento de usuario.

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
        target = path.resolve()
        roots = (references_dir(), voices_dir(), samples_dir(), outputs_dir())
        return str(target) if any(target.is_relative_to(root.resolve()) for root in roots) else None
