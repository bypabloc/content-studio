"""Migraciones de la base (spec 004, D-1): lista de SQL, aplicada en orden según `PRAGMA user_version`."""

from __future__ import annotations

import sqlite3

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
]


def migrate(conn: sqlite3.Connection) -> None:
    """Aplica las migraciones que faltan; cada una y su versión van en una sola transacción."""
    current = conn.execute('PRAGMA user_version').fetchone()[0]
    for version, sql in enumerate(MIGRATIONS[current:], start=current + 1):
        conn.executescript(f'BEGIN;\n{sql}\nPRAGMA user_version = {version};\nCOMMIT;')
