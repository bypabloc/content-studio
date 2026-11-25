"""Servicio diarize: valida el audio, los hablantes y el motor, y arma el comando de job_main (spec 035, AC-7)."""

from content_studio.diarization import diarize_main
from content_studio.services import diarize


def test_ac7_validate_reports_the_missing_file_and_the_engine(tmp_path, monkeypatch):
    monkeypatch.setattr(diarize_main, 'available', lambda: False)

    codes = [error['code'] for error in diarize.validate({'input': str(tmp_path / 'missing.wav')})]

    assert codes == ['file_not_found', 'engine_not_installed']


def test_ac7_validate_rejects_speakers_out_of_range_and_min_over_max(tmp_path, monkeypatch):
    monkeypatch.setattr(diarize_main, 'available', lambda: True)
    audio = tmp_path / 'audio.wav'
    audio.write_bytes(b'RIFF')

    assert diarize.validate({'input': str(audio), 'num_speakers': 21}) == [{'code': 'invalid_speakers', 'params': {}}]
    assert diarize.validate({'input': str(audio), 'min_speakers': 0}) == [{'code': 'invalid_speakers', 'params': {}}]
    assert diarize.validate({'input': str(audio), 'min_speakers': 3, 'max_speakers': 2}) == [
        {'code': 'invalid_speakers', 'params': {}}
    ]
    assert diarize.validate({'input': str(audio), 'num_speakers': 2}) == []


def test_ac7_runs_on_the_gpu_and_passes_the_speaker_flags(tmp_path):
    assert diarize.RESOURCE == 'gpu'

    command = diarize.build_command({'input': 'audio.wav', 'num_speakers': 2, 'max_speakers': 4}, tmp_path)

    assert command[1:3] == ['-m', 'content_studio.diarization.job_main']
    assert command[command.index('--speakers') + 1] == '2'
    assert command[command.index('--max-speakers') + 1] == '4'
    assert '--min-speakers' not in command
    assert command[command.index('--out') + 1] == str(tmp_path)
