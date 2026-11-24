"""Entrada de `subtitles.burn` (spec 014, D-7): los flags, el código 3 sin libass y el informe de la quema."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_studio.subtitles import burn_main
from content_studio.subtitles.document import save
from content_studio.subtitles.sources import from_cleaner

WORDS = [
    {'word': 'hola', 'start': 0.2, 'end': 0.9},
    {'word': 'mundo', 'start': 1.0, 'end': 1.8},
]


def _project(tmp_path: Path) -> Path:
    doc_path = tmp_path / 'subtitles.json'
    save(from_cleaner(WORDS, source_path=str(tmp_path / 'charla.mp4'), language='es'), doc_path)
    return doc_path


def _fake_system(monkeypatch, *, libass: bool) -> None:
    monkeypatch.setattr(burn_main.tools, 'detect', lambda: {'subtitles_filter': libass, 'gpu': None})
    monkeypatch.setattr(burn_main.ff, 'video_size', lambda path: (1080, 1920))


def test_the_preset_flag_only_accepts_the_known_presets():
    """`--preset` solo acepta los presets de `styles.PRESETS`; otro nombre sale con error de argparse."""
    with pytest.raises(SystemExit):
        burn_main.build_parser().parse_args(['--doc', 'a', '--out', 'b', '--preset', 'nope'])


def test_without_libass_the_run_is_refused_and_main_exits_with_code_3(tmp_path, monkeypatch, capsys):
    """Sin el filtro `subtitles` (libass) no se quema: `run` lanza `NoLibass` y `main` sale con `NO_LIBASS` (3)."""
    _fake_system(monkeypatch, libass=False)
    doc_path = _project(tmp_path)

    with pytest.raises(burn_main.NoLibass):
        burn_main.run(doc_path, tmp_path / 'out')

    code = burn_main.main(['--doc', str(doc_path), '--out', str(tmp_path / 'out')])
    assert code == burn_main.NO_LIBASS == 3
    assert 'libass' in capsys.readouterr().err


def test_with_libass_it_writes_the_ass_and_burns_a_copy_of_the_video(tmp_path, monkeypatch):
    """Con libass se escribe `subtitles.ass` y se quema en `subtitled.mp4`; el informe trae el tamaño del video."""
    _fake_system(monkeypatch, libass=True)
    burned = {}

    def fake_burn(source, ass, fonts_dir, destination, **kwargs):
        burned.update(source=source, ass=ass, destination=destination, nvenc=kwargs['nvenc'])

    monkeypatch.setattr(burn_main.burn, 'burn', fake_burn)

    report = burn_main.run(_project(tmp_path), tmp_path / 'out', preset_name='reels')

    ass_text = (tmp_path / 'out' / 'subtitles.ass').read_text(encoding='utf-8')
    assert 'Dialogue:' in ass_text
    assert 'HOLA' in ass_text  # reels escribe en mayúsculas
    assert burned['destination'] == tmp_path / 'out' / 'subtitled.mp4'
    assert burned['nvenc'] is False  # sin GPU detectada, no se usa NVENC
    assert report == {
        'video': str(tmp_path / 'out' / 'subtitled.mp4'),
        'ass': str(tmp_path / 'out' / 'subtitles.ass'),
        'width': 1080,
        'height': 1920,
    }
