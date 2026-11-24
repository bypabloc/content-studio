"""Carga de proyectos de subtítulos referidos por pistas del Editor (spec 019, AC-6)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from content_studio.editor import subtitle_projects


def _doc(project_id: object) -> dict:
    return {'tracks': [{'kind': 'subtitles', 'subtitles_project': project_id}]}


def test_load_documents_skips_tracks_without_subtitles():
    """Las pistas de audio y video no consultan proyectos 014."""
    doc = {'tracks': [{'kind': 'audio', 'subtitles_project': '7'}]}

    assert subtitle_projects.load_documents(doc, sqlite3.connect(':memory:')) == {}


@pytest.mark.parametrize('project_id', [None, 7, '', '0', '-1', 'abc'])
def test_load_documents_rejects_invalid_project_ids(project_id: object):
    """Solo se aceptan IDs decimales positivos en forma de string."""
    with pytest.raises(subtitle_projects.MissingSubtitleProject) as error:
        subtitle_projects.load_documents(_doc(project_id), sqlite3.connect(':memory:'))

    assert error.value.project_id == str(project_id)


def test_load_documents_reads_the_registered_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """El documento se lee desde la ruta registrada por SQLite y se indexa por el ID decimal."""
    path = tmp_path / 'subtitles.json'
    path.write_text('{"version": 1, "cues": []}', encoding='utf-8')
    monkeypatch.setattr(
        subtitle_projects.subtitle_projects,
        'get',
        lambda _conn, project_id: {'doc_path': str(path)} if project_id == 7 else None,
    )

    result = subtitle_projects.load_documents(_doc('7'), sqlite3.connect(':memory:'))

    assert result == {'7': {'version': 1, 'cues': []}}


def test_load_documents_rejects_an_unregistered_project(monkeypatch: pytest.MonkeyPatch):
    """Un ID válido pero ausente en SQLite se informa como proyecto faltante."""
    monkeypatch.setattr(subtitle_projects.subtitle_projects, 'get', lambda _conn, _project_id: None)

    with pytest.raises(subtitle_projects.MissingSubtitleProject, match='subtitle_project_not_found'):
        subtitle_projects.load_documents(_doc('7'), sqlite3.connect(':memory:'))


def test_load_documents_rejects_a_missing_document(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Un registro sin archivo JSON disponible no carga una pista huérfana."""
    missing = tmp_path / 'missing.json'
    monkeypatch.setattr(
        subtitle_projects.subtitle_projects,
        'get',
        lambda _conn, _project_id: {'doc_path': str(missing)},
    )

    with pytest.raises(subtitle_projects.MissingSubtitleProject, match='subtitle_project_not_found'):
        subtitle_projects.load_documents(_doc('7'), sqlite3.connect(':memory:'))
