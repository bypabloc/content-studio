"""`studio llm` (spec 021): parámetros de las tareas y ayuda."""

import pytest

from content_studio.cli import llm
from content_studio.cli.main import build_parser


def test_help_lists_the_tasks(capsys):
    """La ayuda nombra las tareas del asistente."""
    with pytest.raises(SystemExit):
        build_parser().parse_args(['llm', '--help'])
    out = capsys.readouterr().out
    assert 'script-review' in out
    assert 'music-caption' in out


def test_script_review_reads_the_text_or_a_file(tmp_path):
    """--text o --file (UTF-8), --all y --model pasan a los parámetros del trabajo."""
    args = build_parser().parse_args(['llm', 'script-review', '--text', 'Hola.', '--all'])
    assert llm.params(args) == ('llm.script_review', {'text': 'Hola.', 'all': True})

    script = tmp_path / 'guion.txt'
    script.write_text('Tienes 24 horas.', encoding='utf-8')
    args = build_parser().parse_args(['llm', 'script-review', '--file', str(script), '--model', 'qwen3.5-9b'])
    assert llm.params(args) == ('llm.script_review', {'text': 'Tienes 24 horas.', 'all': False, 'model': 'qwen3.5-9b'})


def test_music_caption_takes_the_description():
    """La descripción en español es el único argumento obligatorio."""
    args = build_parser().parse_args(['llm', 'music-caption', 'piano tranquilo'])
    assert llm.params(args) == ('llm.music_caption', {'description': 'piano tranquilo'})


def test_a_failed_job_prints_its_error_code(tmp_path, monkeypatch, capsys):
    """Si el trabajo falla, sale con 1, el código en stdout (JSON) y su texto en stderr."""
    from content_studio.db import connection, jobs, schema

    db = tmp_path / 'base.db'
    conn = connection.connect(db)
    schema.migrate(conn)
    job_id = jobs.insert(conn, 'llm.music_caption', 'gpu', {'description': 'x'})
    jobs.update(conn, job_id, status='error', error_code='llm_not_installed')
    conn.close()
    monkeypatch.setattr(
        llm.submit, 'execute', lambda *a: {'job': job_id, 'status': 'error', 'output_dir': str(tmp_path)}
    )

    code = llm.run(build_parser().parse_args(['--db', str(db), 'llm', 'music-caption', 'piano']))

    assert code == 1
    captured = capsys.readouterr()
    assert '"error_code": "llm_not_installed"' in captured.out
    assert 'Motores' in captured.err or 'Engines' in captured.err


def test_a_done_job_prints_the_result(tmp_path, monkeypatch, capsys):
    """Si termina, imprime result.json tal cual."""
    (tmp_path / 'result.json').write_text('{"caption": "piano, no vocals"}', encoding='utf-8')
    monkeypatch.setattr(llm.submit, 'execute', lambda *a: {'job': 1, 'status': 'done', 'output_dir': str(tmp_path)})

    assert llm.run(build_parser().parse_args(['llm', 'music-caption', 'piano'])) == 0
    assert 'no vocals' in capsys.readouterr().out
