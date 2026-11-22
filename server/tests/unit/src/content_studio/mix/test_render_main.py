import json
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.mix import project, render_main

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def _wav(path: Path, seconds: int) -> Path:
    """Un WAV de `seconds` s con un tono (la voz o la música de prueba)."""
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=440:duration={seconds}',
            str(path),
        ],
        check=True,
    )
    return path


def _project(tmp_path: Path, voice: Path, music: Path) -> Path:
    """Un `mix.json` con la voz de 6 s, intro y outro de 1 s y un tramo de voz al principio."""
    doc = project.new_document(str(voice), str(music), None, 'replace', None)
    doc['regions'] = [[0.0, 1.0]]
    doc['params'] = {**doc['params'], 'intro': 1.0, 'outro': 1.0}
    doc_path = tmp_path / 'mix.json'
    project.save(doc_path, doc)
    return doc_path


@needs_ffmpeg
def test_run_mixes_the_project_into_the_job_folder_with_its_report(tmp_path):
    """El trabajo lee el `mix.json` y deja `mix.wav` y `result.json`, con la duración intro + voz + outro."""
    doc_path = _project(tmp_path, _wav(tmp_path / 'voice.wav', 6), _wav(tmp_path / 'music.wav', 12))
    out_dir = tmp_path / 'job'

    result = render_main.run(doc_path, out_dir)

    assert (out_dir / 'mix.wav').exists()
    assert json.loads((out_dir / 'result.json').read_text(encoding='utf-8'))['output'] == str(out_dir / 'mix.wav')
    assert result['duration'] == pytest.approx(8, abs=0.01)


@needs_ffmpeg
def test_a_music_shorter_than_the_mix_exits_with_its_error_code(tmp_path, capsys):
    """AC-4: con una música de 4 s para 8 s de mezcla, el trabajo sale con 2 y `music_too_short` en stderr."""
    doc_path = _project(tmp_path, _wav(tmp_path / 'voice.wav', 6), _wav(tmp_path / 'music.wav', 4))

    code = render_main.main(['--project', str(doc_path), '--out-dir', str(tmp_path / 'job')])

    assert code == 2
    assert 'music_too_short' in capsys.readouterr().err
