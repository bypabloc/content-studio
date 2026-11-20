"""Trabajo de reubicación de una raíz de almacenamiento."""

from __future__ import annotations

import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from content_studio import paths
from content_studio.common import progress
from content_studio.db import connection, settings
from content_studio.storage import relocate

RESOURCE = 'cpu'
KIND = 'storage.move'
OUTPUT_MOVES = 'storage.outputs_moves'
LOCATIONS = {'engines': paths.engines_dir, 'outputs': paths.outputs_dir}


def validate(params: dict) -> list[dict]:
    """El destino debe ser una carpeta absoluta y el tipo debe ser conocido."""
    if params.get('target') not in tuple(LOCATIONS):
        return [{'code': 'invalid_storage_target', 'params': {}}]
    value = params.get('to')
    if not isinstance(value, str) or '\x00' in value:
        return [{'code': 'invalid_storage_destination', 'params': {}}]
    destination = Path(value)
    if not destination.is_absolute() or destination == Path(destination.anchor):
        return [{'code': 'invalid_storage_destination', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Comando del trabajo, sin serializar parámetros en una línea de shell."""
    return [sys.executable, '-m', __name__, params['target'], params['to']]


def _moves(conn: sqlite3.Connection) -> dict[str, str]:
    value = settings.get(conn, OUTPUT_MOVES, {})
    return value if isinstance(value, dict) else {}


def follow_output_move(path: Path, conn: sqlite3.Connection) -> Path:
    """Apunta al destino actual si esta ruta pertenece a una raíz histórica."""
    for source, target in _moves(conn).items():
        if path.is_relative_to(source):
            return Path(target) / path.relative_to(source)
    return path


def run(kind: str, destination: Path) -> None:
    """Publica la carpeta nueva solo después de un traslado completo."""
    database = paths.db_path()
    source = LOCATIONS[kind](database).resolve()
    if destination.is_symlink():
        raise ValueError('Storage target must be a real directory')
    target = destination.resolve()
    if source == target:
        return
    protected = (database.resolve(), paths.references_dir().resolve(), paths.voices_dir().resolve())
    if any(item.is_relative_to(root) for item in protected for root in (source, target)):
        raise ValueError('Storage cannot contain the database, references or voices')
    other = LOCATIONS['engines' if kind == 'outputs' else 'outputs'](database).resolve()
    if target.is_relative_to(other) or other.is_relative_to(target):
        raise ValueError('Engines and output directories must be separate')

    def save() -> None:
        with closing(connection.connect(database)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            if kind == 'outputs':
                moves = {old: str(target) for old in _moves(conn) if old != str(target)}
                moves[str(source)] = str(target)
                settings.set_value(conn, OUTPUT_MOVES, moves)
            settings.set_value(conn, f'storage.{kind}', str(target))
            conn.commit()

    relocate.move(source, target, save, lambda fraction: progress.emit(fraction, 'copying'))
    progress.emit(1, 'done')


if __name__ == '__main__':
    run(sys.argv[1], Path(sys.argv[2]))
