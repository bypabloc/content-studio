"""Un test por bug corregido del análisis. Corre con: uv run --with pytest pytest tests"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
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
    studio = ['-m', 'content_studio.cli.main', 'music', '--help']
    for args in (['-m', 'content_studio.music.music_main', '--help'], studio):
        r = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True)
        assert r.returncode == 0, r.stderr.decode('cp1252', 'replace')


def test_cc_by_voices_have_attribution():
    from content_studio.narration.voices.catalog import catalog, mention

    no = [n for n, f in catalog().items() if 'BY' in f['license'] and not mention(f)]
    assert not no, f'licencia CC BY sin "atribucion" en catalog.json: {no}'


def test_recording_kit_covers_the_tts_styles():
    from content_studio.narration.recording_kit import KIT, OPTIONAL
    from content_studio.narration.styles import STYLES

    assert set(STYLES) <= {row[0] for row in KIT + OPTIONAL}


def test_reference_folder_is_reference():
    """paths.REFERENCE apuntaba a narration/voice; la carpeta migrada es reference/."""
    from content_studio import paths

    assert paths.REFERENCE == paths.NARRATION / 'reference'
    assert paths.TAKES == paths.REFERENCE / 'takes'


def test_approval_reads_the_english_keys(tmp_path, monkeypatch):
    """aprobacion.json usa claves en inglés desde la migración (WARNING 002-voces-migracion)."""
    import json

    from content_studio import paths
    from content_studio.narration.voices import catalog

    voices = tmp_path / 'voices'
    (voices / 'ana').mkdir(parents=True)
    (voices / 'ana' / 'neutral.wav').write_bytes(b'RIFF')
    (voices / 'ana' / 'aprobacion.json').write_text(
        json.dumps({'voice': 'ana', 'approved': True, 'styles': {'neutral': {'ok': True}}}), encoding='utf-8'
    )
    (voices / 'catalog.json').write_text(json.dumps({'ana': {'license': 'CC0'}}), encoding='utf-8')
    monkeypatch.setattr(paths, 'VOICES', voices)
    monkeypatch.setattr(catalog, 'CATALOG', voices / 'catalog.json')
    assert list(catalog.approved_voices(['neutral'])) == ['ana']
    assert catalog.state('ana', ['neutral']) == 'approved'


def test_server_launched_from_an_mcp_client_breaks_away_from_its_job(tmp_path, monkeypatch):
    """Spec 033: el SDK de MCP mete `studio mcp` en un Job Object con KILL_ON_JOB_CLOSE; el server que lanza lo
    heredaba y moría al cerrar el cliente, con los trabajos a medias. Ahora pide salir del job y, si el job no lo
    permite, arranca igual."""
    import subprocess

    from content_studio.runtime import instance

    breakaway = getattr(subprocess, 'CREATE_BREAKAWAY_FROM_JOB', 0x01000000)
    seen: list[int] = []

    def popen(command, **kwargs):
        flags = kwargs.get('creationflags', 0)
        seen.append(flags)
        if flags & breakaway and len(seen) == 1:
            raise PermissionError(5, 'access denied: the job does not allow breakaway')
        return None

    monkeypatch.setattr(instance.os, 'name', 'nt')
    monkeypatch.setattr(instance.subprocess, 'Popen', popen)
    monkeypatch.setattr(instance, 'log_path', lambda: tmp_path / 'server.log')

    instance._launch(tmp_path / 'base.db', None)

    assert seen[0] & breakaway
    assert not seen[1] & breakaway
    assert len(seen) == 2


def test_narration_without_style_uses_the_default_of_the_engine():
    """021-estilo-none-en-txt: sin --style, el trabajo no falla con «No existe el estilo None» y el motor usa su valor
    por defecto (el style del JSON o expert)."""
    from content_studio.services import narration

    params = {'model': 'qwen-0.6b', 'file': ['guion.txt']}
    codes = [error['code'] for error in narration.validate(params)]
    assert 'unknown_style' not in codes
    assert '--style' not in narration.build_command(params, Path('out'))


def test_studio_json_reaches_a_pipe_as_utf8():
    """021-cli-salida-cp1252: con stdout en una tubería, las tildes salen en UTF-8, no en cp1252."""
    import os
    import subprocess

    code = 'from content_studio.common.process import console_utf8; console_utf8(); print("guía")'
    env = {key: value for key, value in os.environ.items() if key not in ('PYTHONIOENCODING', 'PYTHONUTF8')}
    env['PYTHONPATH'] = str(ROOT / 'server' / 'src')
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, env=env, check=True).stdout
    assert out.decode('utf-8').strip() == 'guía'
