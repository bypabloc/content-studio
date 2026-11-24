"""Carga documentos 014 referenciados por pistas del proyecto del Editor."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from content_studio.db import subtitle_projects
from content_studio.subtitles.document import load


class MissingSubtitleProject(ValueError):
    """La pista refiere un proyecto que ya no está registrado o guardado."""

    def __init__(self, project_id: str) -> None:
        """Conserva el ID decimal que no pudo resolverse."""
        super().__init__('subtitle_project_not_found')
        self.project_id = project_id


def load_documents(doc: dict[str, Any], conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Carga cada documento de subtítulos persistido por la pista, indexado por su ID decimal."""
    documents = {}
    for track in doc.get('tracks', []):
        if track.get('kind') != 'subtitles':
            continue
        project_id = track.get('subtitles_project')
        if not isinstance(project_id, str) or not project_id.isdecimal() or int(project_id) < 1:
            raise MissingSubtitleProject(str(project_id))
        row = subtitle_projects.get(conn, int(project_id))
        if row is None:
            raise MissingSubtitleProject(project_id)
        path = Path(row['doc_path'])
        if not path.is_file():
            raise MissingSubtitleProject(project_id)
        documents[project_id] = load(path)
    return documents
