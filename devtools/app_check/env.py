"""La carpeta y el entorno de una corrida de `app-check` (spec 024, D-3 y D-4).

Cada corrida vive en `tmp/app-check/<AAAAMMDD-HHMMSS>/` del worktree: su carpeta de datos de WebView2 (dos instancias
con la misma carpeta fallan con 0x800700AA), su home y su base, sus salidas y sus capturas. El binario se compila en
`tmp/app-check/cargo-target` del worktree: `project_root()` de Tauri se fija al compilar, así que un target
compartido abriría el server de otro checkout.

`temp` arranca de cero. `real` muestra los motores, voces y salidas del usuario sobre una copia de su base con la cola
en pausa: el worker de esta instancia no corre los trabajos del usuario, y Playwright aborta las escrituras.
"""

from __future__ import annotations

import socket
import sqlite3
import sys
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# La base usa el esquema y las preferencias del server (solo stdlib): se importan sin su venv, como en gpu_turn.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'server' / 'src'))
from content_studio.db import settings  # noqa: E402
from content_studio.db.schema import migrate  # noqa: E402, F401  (los tests crean bases con el mismo esquema)

MODES = ('temp', 'real')
# La misma clave que jobs/queue.py; queue.py no se importa porque arrastra el registro de servicios.
PAUSED = 'queue.paused'


class AppCheckError(Exception):
    """Un problema de la corrida que se informa con exit 2."""


@dataclass(frozen=True)
class Run:
    """Una corrida: su carpeta, las variables que la aíslan, el puerto de CDP y el modo de datos."""

    dir: Path
    env: dict[str, str]
    port: int
    data: str
    db: str


def free_port() -> int:
    """Un puerto libre de 127.0.0.1, el que elige el sistema (como `pick_free_port` de `studio serve`)."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _fresh_db(path: Path, outputs: Path | None, paused: bool) -> None:
    """Base nueva con el esquema del server; las salidas van a `outputs` si se da."""
    with closing(sqlite3.connect(path)) as conn, conn:
        migrate(conn)
        if outputs is not None:
            settings.set_value(conn, 'storage.outputs', outputs.as_posix())
        if paused:
            settings.set_value(conn, PAUSED, True)
        # La bienvenida taparía las secciones; se prueba con su propio escenario o con su e2e.
        settings.set_value(conn, 'welcome.done', True)


def _paused_copy(source: Path, path: Path) -> None:
    """Copia consistente (también con WAL) de la base del usuario, con la cola en pausa. La original no se escribe."""
    readonly = f'{source.resolve().as_uri()}?mode=ro'
    with closing(sqlite3.connect(readonly, uri=True)) as src, closing(sqlite3.connect(path)) as dst, dst:
        src.backup(dst)
        settings.set_value(dst, PAUSED, True)


def prepare(root: Path, data: str, now: datetime, source_db: Path | None = None, outputs: Path | None = None) -> Run:
    """Crea la carpeta de la corrida y devuelve el entorno que la aísla, sin tocar `os.environ`.

    En `real`, `source_db` es la base del usuario: se copia en pausa. Si no existe (la app nunca se abrió desde el
    checkout), la base es nueva y en pausa, con las salidas del usuario (`outputs`) para verlas igual.
    """
    if data not in MODES:
        raise AppCheckError(f'--data must be one of {", ".join(MODES)}, not {data!r}')
    base = root / 'tmp' / 'app-check'
    run_dir = base / now.strftime('%Y%m%d-%H%M%S')
    for sub in ('webview2', 'shots'):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    db = run_dir / 'content-studio.db'
    port = free_port()
    env = {
        'WEBVIEW2_USER_DATA_FOLDER': str(run_dir / 'webview2'),
        'WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS': f'--remote-debugging-port={port}',
        'CONTENT_STUDIO_DB': str(db),
        'CARGO_TARGET_DIR': str(base / 'cargo-target'),
    }
    if data == 'temp':
        (run_dir / 'home').mkdir(exist_ok=True)
        (run_dir / 'out').mkdir(exist_ok=True)
        env['CONTENT_STUDIO_HOME'] = str(run_dir / 'home')
        _fresh_db(db, run_dir / 'out', paused=False)
        return Run(run_dir, env, port, data, 'fresh')
    source = source_db if source_db is not None else root / 'var' / 'content-studio.db'
    if source.is_file():
        _paused_copy(source, db)
        return Run(run_dir, env, port, data, 'copy')
    _fresh_db(db, outputs if outputs is not None and outputs.is_dir() else None, paused=True)
    return Run(run_dir, env, port, data, 'fresh')
