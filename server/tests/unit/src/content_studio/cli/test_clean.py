"""CLI `studio clean` (spec 013, D-2 y D-4): valida los medios antes de encolar y, con `--auto`, renderiza."""

from __future__ import annotations

from pathlib import Path

import pytest

import content_studio.cli.main as cli_main
from content_studio.cli import submit
from content_studio.cli.main import main
from content_studio.db import connection, schema
from content_studio.transcription import models


@pytest.fixture
def db(tmp_path) -> str:
    path = tmp_path / 'base.db'
    conn = connection.connect(path)
    schema.migrate(conn)
    conn.close()
    return str(path)


@pytest.fixture
def media(tmp_path) -> Path:
    path = tmp_path / 'charla.mp4'
    path.write_bytes(b'')  # `studio clean` solo mira que exista y su extensión: el análisis no corre en estos tests
    return path


def _fake_jobs(monkeypatch, status: str = 'done') -> list[tuple[str, dict]]:
    """Reemplaza el encolado: anota cada trabajo que `studio clean` pide, sin correr motores."""
    requested: list[tuple[str, dict]] = []

    def execute(kind, params, db, main):
        requested.append((kind, params))
        return {'job': len(requested), 'status': status, 'output_dir': f'out/analysis-{len(requested)}'}

    def run(kind, params, db, main):
        requested.append((kind, params))
        return 0

    monkeypatch.setattr(submit, 'execute', execute)
    monkeypatch.setattr(submit, 'run', run)
    monkeypatch.setattr(cli_main, 'main_checkout', lambda start: Path('.'))
    return requested


def test_help_shows_the_auto_flag(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['clean', '--help'])

    assert exit_info.value.code == 0
    assert '--auto' in capsys.readouterr().out


def test_analyze_uses_the_recommended_model_by_default(media, db, monkeypatch):
    requested = _fake_jobs(monkeypatch)

    assert main(['clean', str(media), '--db', db]) == 0

    assert requested == [
        (
            'clean.analyze',
            {
                'input': str(media),
                'model': models.recommended(),
                'language': 'auto',
                'min_gap': 0.5,
                'padding': 0.15,
                'edges': True,
            },
        )
    ]


def test_without_auto_the_cut_is_only_analyzed(media, db, monkeypatch):
    requested = _fake_jobs(monkeypatch)

    main(['clean', str(media), '--db', db])

    assert [kind for kind, _ in requested] == ['clean.analyze']


def test_auto_renders_the_analysis_folder(media, db, monkeypatch):
    requested = _fake_jobs(monkeypatch)

    assert main(['clean', str(media), '--auto', '--db', db]) == 0

    assert requested[1] == ('clean.render', {'input': str(media), 'analysis': 'out/analysis-1'})


def test_no_edges_turns_off_the_edge_cuts(media, db, monkeypatch):
    requested = _fake_jobs(monkeypatch)

    main(['clean', str(media), '--no-edges', '--db', db])

    assert requested[0][1]['edges'] is False


def test_a_failed_analysis_is_not_rendered(media, db, monkeypatch):
    requested = _fake_jobs(monkeypatch, status='error')

    assert main(['clean', str(media), '--auto', '--db', db]) == 1

    assert [kind for kind, _ in requested] == ['clean.analyze']


def test_a_missing_file_exits_2_before_queueing(tmp_path, db, monkeypatch, capsys):
    requested = _fake_jobs(monkeypatch)
    missing = tmp_path / 'no-existe.mp4'

    assert main(['clean', str(missing), '--db', db]) == 2

    assert requested == []
    assert 'no-existe.mp4' in capsys.readouterr().err


def test_an_unsupported_format_exits_2_before_queueing(tmp_path, db, monkeypatch, capsys):
    requested = _fake_jobs(monkeypatch)
    notes = tmp_path / 'notas.txt'
    notes.write_text('no es audio', encoding='utf-8')

    assert main(['clean', str(notes), '--db', db]) == 2

    assert requested == []
    assert 'notas.txt' in capsys.readouterr().err
