"""Migraciones de la base (spec 004, D-1): lista de SQL, aplicada en orden según `PRAGMA user_version`."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

KEEP_BACKUPS = 5

MIGRATIONS = [
    """
    CREATE TABLE jobs (
      id INTEGER PRIMARY KEY,
      kind TEXT NOT NULL,
      resource TEXT NOT NULL CHECK (resource IN ('gpu', 'cpu')),
      status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'done', 'error', 'cancelled')),
      position INTEGER NOT NULL,
      params TEXT NOT NULL,
      output_dir TEXT,
      result TEXT,
      error_code TEXT,
      error_detail TEXT,
      progress REAL NOT NULL DEFAULT 0,
      stage TEXT,
      created_at TEXT NOT NULL,
      started_at TEXT,
      finished_at TEXT
    );
    CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
    """,
    # El pid que corre el trabajo: al arrancar, el server solo interrumpe los de procesos que ya no viven.
    """
    ALTER TABLE jobs ADD COLUMN owner_pid INTEGER;
    """,
    # Spec 006 (D-4): tomas de un mismo texto, con su clave de grupo y la elegida. Es la 3: la 2 es owner_pid.
    """
    ALTER TABLE jobs ADD COLUMN starred INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE jobs ADD COLUMN group_key TEXT;
    CREATE INDEX jobs_group_key ON jobs (group_key);
    """,
    # Spec 013 (D-4): caché de transcripciones. Solo rutas y metadatos; el texto va en el JSON de su ruta. Es la 4:
    # la 3 ya es starred y group_key.
    """
    CREATE TABLE transcripts (
      id INTEGER PRIMARY KEY,
      source_path TEXT NOT NULL,
      source_mtime REAL NOT NULL,
      source_size INTEGER NOT NULL,
      model TEXT NOT NULL,
      language TEXT NOT NULL,
      json_path TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE INDEX transcripts_source ON transcripts (source_path, model, language);
    """,
    # Spec 014 (D-1): proyectos de subtítulos, solo nombre y rutas. Es la 5: la 4 ya es la caché de la 013.
    """
    CREATE TABLE subtitle_projects (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      source_path TEXT NOT NULL,
      doc_path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    """,
    # Spec 016 (D-3): proyectos de mezcla, solo nombre y ruta del documento. Es la 6: la 5 ya es subtítulos (014).
    """
    CREATE TABLE mix_projects (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      doc_path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    """,
    # Spec 020 (D-1): la biblioteca. Solo rutas, metadatos numéricos, etiquetas y relaciones; nada de contenido. Es la
    # 7: la 6 ya es mezcla (016). Las miniaturas van en una caché de disco y el texto se lee de los JSON en disco.
    """
    CREATE TABLE library_folders (id INTEGER PRIMARY KEY, path TEXT NOT NULL UNIQUE, name TEXT, added_at TEXT NOT NULL);
    CREATE TABLE library_items (
      id INTEGER PRIMARY KEY,
      path TEXT NOT NULL UNIQUE,
      kind TEXT NOT NULL,
      origin TEXT NOT NULL CHECK (origin IN ('job', 'watched')),
      job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
      folder_id INTEGER REFERENCES library_folders(id) ON DELETE CASCADE,
      size INTEGER NOT NULL,
      mtime REAL NOT NULL,
      duration REAL,
      width INTEGER,
      height INTEGER,
      media_type TEXT NOT NULL CHECK (media_type IN ('audio', 'video', 'subtitle', 'other')),
      missing INTEGER NOT NULL DEFAULT 0,
      indexed_at TEXT NOT NULL
    );
    CREATE INDEX library_items_kind ON library_items (kind);
    CREATE INDEX library_items_mtime ON library_items (mtime);
    CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
    CREATE TABLE item_tags (
      item_id INTEGER REFERENCES library_items(id) ON DELETE CASCADE,
      tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
      PRIMARY KEY (item_id, tag_id)
    );
    CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE project_items (
      project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
      item_id INTEGER REFERENCES library_items(id) ON DELETE CASCADE,
      PRIMARY KEY (project_id, item_id)
    );
    """,
    # 8 (spec 021, D-4): la ruta de publish.json del ítem; el contenido queda en disco.
    'ALTER TABLE library_items ADD COLUMN publish_path TEXT;',
]


def migrate(conn: sqlite3.Connection, backups: Path | None = None) -> None:
    """Aplica las migraciones que faltan; cada una y su versión van en una sola transacción.

    Con `backups` (spec 022, D-4), una base con datos se respalda antes en `<backups>/<fecha>-v<anterior>.db` (quedan
    los 5 últimos); si una migración falla, la base vuelve a ese respaldo y el error sigue.
    """
    current = conn.execute('PRAGMA user_version').fetchone()[0]
    if current >= len(MIGRATIONS):
        return
    saved = _backup(conn, backups, current) if backups is not None and current else None
    try:
        for version, sql in enumerate(MIGRATIONS[current:], start=current + 1):
            conn.executescript(f'BEGIN;\n{sql}\nPRAGMA user_version = {version};\nCOMMIT;')
    except sqlite3.Error:
        if saved is not None:
            if conn.in_transaction:
                conn.rollback()
            with closing(sqlite3.connect(saved)) as copy:
                copy.backup(conn)
        raise


def _backup(conn: sqlite3.Connection, folder: Path, version: int) -> Path:
    """Copia la base con la API de respaldo de SQLite y borra los respaldos más viejos que los 5 últimos."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{datetime.now():%Y-%m-%d-%H%M%S}-v{version}.db'
    with closing(sqlite3.connect(target)) as copy:
        conn.backup(copy)
    for old in sorted(folder.glob('*.db'))[:-KEEP_BACKUPS]:
        old.unlink()
    return target
