"""Búsqueda en el contenido (spec 020, D-2 y AC-3): lee guiones y transcripciones en disco; la base no guarda texto."""

from __future__ import annotations

import itertools
import json
from contextlib import closing
from pathlib import Path

from content_studio.db import connection, jobs, schema
from content_studio.library import index, text_search
from content_studio.transcription import cache

COUNTER = itertools.count()


def _db(tmp_path: Path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def _job(conn, tmp_path: Path, kind: str, files: dict[str, object]) -> int:
    out = tmp_path / 'out' / kind / str(next(COUNTER))
    out.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out / name).write_text(content if isinstance(content, str) else json.dumps(content), encoding='utf-8')
    job_id = jobs.insert(conn, kind, 'cpu', {})
    jobs.update(conn, job_id, status='done', output_dir=str(out))
    return index.register_job(conn, jobs.get(conn, job_id))[0]


def test_ac3_finds_the_narration_script_and_the_cleaned_transcript(tmp_path):
    """AC-3: «registrado» está en el `script.json` de una narración y en el `transcript.json` de un limpio."""
    with closing(_db(tmp_path)) as conn:
        narration = _job(conn, tmp_path, 'narration', {
            'take.srt': '', 'script.json': {'ref': 'x', 'segments': [{'text': 'Quedó REGISTRADO en el acta.'}]},
        })  # fmt: skip
        cleaned = _job(conn, tmp_path, 'clean.render', {
            'clean.srt': '', 'transcript.json': [{'word': ' fue'}, {'word': ' registrado'}],
        })  # fmt: skip
        _job(conn, tmp_path, 'music', {'track.srt': ''})

        assert text_search.matching_ids(conn, 'registrado') == {narration, cleaned}
        assert text_search.matching_ids(conn, 'fue registrado') == {cleaned}


def test_the_narration_settings_are_not_searched(tmp_path):
    """En `script.json` solo cuenta el texto de los segmentos, no las rutas ni el estilo."""
    with closing(_db(tmp_path)) as conn:
        _job(conn, tmp_path, 'narration', {'take.srt': '', 'script.json': {'style': 'expert', 'segments': []}})

        assert text_search.matching_ids(conn, 'expert') == set()


def test_a_cached_transcript_of_the_file_also_matches(tmp_path):
    """La caché de transcripciones (013) cuenta para el archivo transcrito, sea salida o de una carpeta vigilada."""
    with closing(_db(tmp_path)) as conn:
        item = _job(conn, tmp_path, 'media.convert', {'clip.srt': ''})
        source = conn.execute('SELECT path FROM library_items WHERE id = ?', (item,)).fetchone()[0]
        doc = tmp_path / 'transcripts' / 'clip.json'
        doc.parent.mkdir()
        doc.write_text(json.dumps({'segments': [{'text': 'hola mundo', 'words': []}]}), encoding='utf-8')
        cache.store(conn, source, 1.0, 1, 'large-v3-turbo', 'es', str(doc))

        assert text_search.matching_ids(conn, 'MUNDO') == {item}


def test_unreadable_files_and_an_exhausted_time_limit_give_no_error(tmp_path):
    """Un JSON roto no rompe la búsqueda; con el límite de tiempo agotado devuelve lo que alcanzó (nada)."""
    with closing(_db(tmp_path)) as conn:
        _job(conn, tmp_path, 'narration', {'take.srt': '', 'script.json': '{roto'})

        assert text_search.matching_ids(conn, 'roto') == set()
        assert text_search.matching_ids(conn, 'x', seconds=0) == set()
