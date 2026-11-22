"""Análisis del limpiador (spec 013, D-4 y AC-6): transcribe con caché y escribe cuts.json (transcriptor simulado)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.clean import analyze_main, cuts
from content_studio.db import schema
from content_studio.db.connection import connect

PARAMS = {'min_gap': 0.5, 'padding': 0.15, 'edges': True}
# Transcripción simulada: las palabras de AC-1 en un audio de 3.5 s.
TRANSCRIPT = {
    'language': 'es',
    'language_probability': 0.99,
    'duration': 3.5,
    'segments': [
        {
            'start': 0.0,
            'end': 2.3,
            'text': 'hola mundo buenas',
            'words': [
                {'start': 0.0, 'end': 0.4, 'word': 'hola', 'probability': 0.9},
                {'start': 1.2, 'end': 1.6, 'word': 'mundo', 'probability': 0.9},
                {'start': 1.9, 'end': 2.3, 'word': 'buenas', 'probability': 0.9},
            ],
        }
    ],
}


class FakeTranscriber:
    """Hace de la transcripción: escribe el JSON y cuenta cuántas veces corrió (la GPU no se usa en la prueba)."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, source: Path, json_file: Path) -> None:
        self.calls += 1
        json_file.parent.mkdir(parents=True, exist_ok=True)
        json_file.write_text(json.dumps(TRANSCRIPT), encoding='utf-8')


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(tmp_path / 'home'))
    database = connect(tmp_path / 'content-studio.db')
    schema.migrate(database)
    return database


@pytest.fixture
def source(tmp_path) -> Path:
    path = tmp_path / 'entrada.wav'
    path.write_bytes(b'RIFF-fake-audio')
    return path


def test_ac5_the_analysis_writes_the_cuts_document_in_the_job_folder(conn, source, tmp_path):
    """El análisis escribe cuts.json con los parámetros, la duración y los cortes de AC-1."""
    folder = tmp_path / 'job'
    result = analyze_main.run(
        conn, source, model='small', language='es', params=PARAMS, folder=folder, transcribe=FakeTranscriber()
    )

    document = cuts.load(folder)
    assert result == {'cuts': 2, 'duration': 3.5, 'cached': False}
    assert document['params'] == PARAMS
    assert [(c['start'], c['end']) for c in document['cuts']] == [(0.55, 1.05), (2.45, 3.35)]
    assert all(c['enabled'] and not c.get('edited') for c in document['cuts'])


def test_ac6_a_second_analysis_of_the_same_file_does_not_transcribe_again(conn, source, tmp_path):
    """AC-6: con acierto en la caché no se vuelve a transcribir; el resultado queda igual."""
    transcriber = FakeTranscriber()
    analyze_main.run(
        conn, source, model='small', language='es', params=PARAMS, folder=tmp_path / 'a', transcribe=transcriber
    )

    result = analyze_main.run(
        conn, source, model='small', language='es', params=PARAMS, folder=tmp_path / 'b', transcribe=transcriber
    )

    assert transcriber.calls == 1
    assert result['cached'] is True
    assert cuts.load(tmp_path / 'b')['cuts'] == cuts.load(tmp_path / 'a')['cuts']


def test_ac6_another_model_transcribes_again(conn, source, tmp_path):
    """Con otro modelo no hay acierto y se transcribe de nuevo."""
    transcriber = FakeTranscriber()
    analyze_main.run(
        conn, source, model='small', language='es', params=PARAMS, folder=tmp_path / 'a', transcribe=transcriber
    )

    analyze_main.run(
        conn, source, model='medium', language='es', params=PARAMS, folder=tmp_path / 'b', transcribe=transcriber
    )

    assert transcriber.calls == 2
