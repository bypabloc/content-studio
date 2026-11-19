"""Un test por bug corregido del análisis. Corre con: uv run --with pytest pytest tests"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'server' / 'data' / 'narration'), str(ROOT / 'server' / 'data' / 'music')]


def test_takes_max_mas_uno(tmp_path):
    from content_studio.common.files import next_number

    assert next_number(tmp_path, 'neutral') == 1
    for n in ['neutral-1', 'neutral-3', 'neutral-en-7', 'neutral-fin-9', 'neutral-x']:
        (tmp_path / f'{n}.wav').touch()
    assert next_number(tmp_path, 'neutral') == 4  # contando daba 6, y con huecos pisaba una toma


def test_music_failure_does_not_leave_the_old_wav(tmp_path, monkeypatch):
    import pytest

    from content_studio.music import music_main as music
    from content_studio.music.engines.base import MusicEngine, MusicSpec

    class Failure(MusicEngine):  # el motor "falla": no escribe nada
        def generate(self, jobs, a):
            pass

    old = tmp_path / 'acestep-lofi-chill.wav'
    old.write_bytes(b'corrida anterior')
    monkeypatch.setattr(music.process, 'use_venv', lambda *a, **k: None)
    monkeypatch.setattr(MusicSpec, 'create', lambda spec: Failure(spec))
    monkeypatch.setattr(sys, 'argv', ['musica.py', '--model', 'acestep', '--folder', str(tmp_path)])
    with pytest.raises(SystemExit) as e:
        music.main()
    assert e.value.code and 'acestep-lofi-chill.wav' in str(e.value.code)
    assert not old.exists()


def test_tts_output_folder_con_un_script(tmp_path):
    from argparse import Namespace

    import pytest

    from content_studio.narration.script import plan

    a = Namespace(style=None, language='es', model='voxcpm2', output=tmp_path)  # carpeta existente
    assert [s for *_, s in plan(a, [('g', 'Hola', None)])] == [tmp_path / 'g-voxcpm2.wav']
    a.output = tmp_path / 'toma.wav'
    assert [s for *_, s in plan(a, [('g', 'Hola', None)])] == [a.output]
    a.output = tmp_path / 'toma.mp3'
    with pytest.raises(SystemExit):
        plan(a, [('g', 'Hola', None)])


def test_tts_warns_before_overwrite(tmp_path, capsys):
    from content_studio.narration.script import warn_overwrite

    (tmp_path / 'a.wav').touch()
    warn_overwrite([('t', 'expert', tmp_path / 'a.wav'), ('t', 'expert', tmp_path / 'b.wav')])
    err = capsys.readouterr().err
    assert 'a.wav' in err and 'b.wav' not in err


def test_help_en_cp1252():
    import os
    import subprocess

    env = {**os.environ, 'PYTHONIOENCODING': 'cp1252', 'PYTHONPATH': str(ROOT / 'server' / 'src')}
    for args in (['-m', 'content_studio.music.music_main', '--help'], ['cli.py', 'music', '--help']):
        r = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True)
        assert r.returncode == 0, r.stderr.decode('cp1252', 'replace')


def test_cc_by_voices_have_attribution():
    from content_studio.narration.voices.catalog import catalog, mention

    no = [n for n, f in catalog().items() if 'BY' in f['license'] and not mention(f)]
    assert not no, f'licencia CC BY sin "atribucion" en catalog.json: {no}'


def test_recording_kit_covers_the_tts_styles():
    from content_studio.narration.grabar.kit import DURATION  # cspell:ignore grabar
    from content_studio.narration.styles import STYLES

    assert set(STYLES) <= set(DURATION)


def test_reference_folder_is_reference():
    """paths.REFERENCE apuntaba a narration/voice; la carpeta migrada es reference/."""
    from content_studio import paths

    assert paths.REFERENCE == paths.NARRATION / 'reference'
    assert paths.TAKES == paths.REFERENCE / 'takes'
