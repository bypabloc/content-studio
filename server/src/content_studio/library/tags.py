"""Etiquetas de la biblioteca (spec 020, D-3): nombres libres, creados al usarlos; la base guarda solo el nombre."""

from __future__ import annotations

import sqlite3


def _name(value: str) -> str:
    """El nombre sin espacios de más. ValueError si queda vacío."""
    name = ' '.join(value.split())
    if not name:
        raise ValueError('empty tag')
    return name


def _exists(conn: sqlite3.Connection, item_id: int) -> None:
    if conn.execute('SELECT 1 FROM library_items WHERE id = ?', (item_id,)).fetchone() is None:
        raise LookupError(f'item {item_id} does not exist')


def of_item(conn: sqlite3.Connection, item_id: int) -> list[str]:
    """Las etiquetas del ítem, por nombre."""
    rows = conn.execute(
        'SELECT t.name FROM item_tags it JOIN tags t ON t.id = it.tag_id WHERE it.item_id = ? ORDER BY t.name',
        (item_id,),
    )
    return [row[0] for row in rows]


def add(conn: sqlite3.Connection, item_id: int, value: str) -> list[str]:
    """Etiqueta el ítem (crea la etiqueta si hace falta) y devuelve sus etiquetas. LookupError si no existe el ítem."""
    name = _name(value)
    _exists(conn, item_id)
    conn.execute('INSERT INTO tags (name) VALUES (?) ON CONFLICT(name) DO NOTHING', (name,))
    tag_id = conn.execute('SELECT id FROM tags WHERE name = ?', (name,)).fetchone()[0]
    conn.execute('INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?, ?)', (item_id, tag_id))
    return of_item(conn, item_id)


def remove(conn: sqlite3.Connection, item_id: int, value: str) -> list[str]:
    """Quita la etiqueta del ítem y devuelve las que le quedan. LookupError si no existe el ítem."""
    _exists(conn, item_id)
    conn.execute(
        'DELETE FROM item_tags WHERE item_id = ? AND tag_id IN (SELECT id FROM tags WHERE name = ?)',
        (item_id, ' '.join(value.split())),
    )
    return of_item(conn, item_id)


def list_tags(conn: sqlite3.Connection) -> list[dict]:
    """Las etiquetas en uso con cuántos ítems tiene cada una, por nombre."""
    rows = conn.execute(
        'SELECT t.name, COUNT(it.item_id) FROM tags t JOIN item_tags it ON it.tag_id = t.id '
        'GROUP BY t.id ORDER BY t.name'
    )
    return [{'name': name, 'count': count} for name, count in rows]
