"""Servicio diarize.split: necesita el audio y una carpeta con turns.json, y corre en la CPU (spec 035, AC-5)."""

import json

from content_studio.services import diarize_split


def test_ac5_split_needs_the_audio_and_a_diarization_folder(tmp_path):
    codes = [
        error['code']
        for error in diarize_split.validate({'input': str(tmp_path / 'missing.wav'), 'turns': str(tmp_path)})
    ]

    assert codes == ['file_not_found', 'not_a_diarization']


def test_ac5_split_is_valid_with_audio_and_turns(tmp_path):
    audio = tmp_path / 'audio.wav'
    audio.write_bytes(b'RIFF')
    (tmp_path / 'turns.json').write_text(json.dumps({'speakers': []}), encoding='utf-8')

    assert diarize_split.validate({'input': str(audio), 'turns': str(tmp_path)}) == []


def test_ac5_split_runs_on_the_cpu_through_job_main(tmp_path):
    assert diarize_split.RESOURCE == 'cpu'

    command = diarize_split.build_command({'input': 'a.wav', 'turns': str(tmp_path)}, tmp_path / 'out')

    assert command[1:3] == ['-m', 'content_studio.diarization.job_main']
    assert command[3] == 'split'
