"""Chequeo de una toma de voz propia (spec 010, D-3 y AC-4): WAVs sintéticos y una transcripción simulada."""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf

from content_studio import paths
from content_studio.narration import profiles
from content_studio.services import voice_check

SR = 48000
TEXT = 'Mira, el problema real no es la cámara: es la falta de una idea clara.'


def make_take(path, *, seconds=10.0, peak_db=-9.0, edge=0.4, pause=0.0, noise_db=None):
    """Un WAV de 48 kHz: silencio de `edge` s en cada borde y voz (un tono). `pause` mete un silencio interno y
    `noise_db` pone ruido de sala en el borde inicial."""
    samples = np.zeros(int(SR * seconds), dtype=np.float32)
    t = np.arange(int(SR * (seconds - 2 * edge))) / SR
    voice = (np.sin(2 * np.pi * 220 * t) * 10 ** (peak_db / 20)).astype(np.float32)
    if pause:
        middle = len(voice) // 2
        voice[middle : middle + int(SR * pause)] = 0
    samples[int(SR * edge) : int(SR * edge) + len(voice)] = voice
    if noise_db is not None:
        rng = np.random.default_rng(7)
        samples[: int(SR * edge)] = rng.normal(0, 10 ** (noise_db / 20), int(SR * edge))
    sf.write(path, samples, SR, subtype='PCM_24')
    return path


def heard(text):
    """Una transcripción simulada: whisper oye `text` (o no está, si es None)."""
    return lambda path: text


@pytest.fixture
def refs(tmp_path, monkeypatch):
    """Una carpeta de referencias vacía en lugar de server/data/narration/reference/."""
    root = tmp_path / 'reference'
    root.mkdir()
    monkeypatch.setattr(paths, 'REFERENCE', root)
    return root


def test_ac4_a_take_that_meets_every_criterion_is_ok(tmp_path):
    wav = make_take(tmp_path / 'ok.wav')

    result = voice_check.check_take(wav, 'expert', TEXT, heard(TEXT))

    assert result['verdict'] == 'ok' and result['reasons'] == []


def test_ac4_a_peak_of_minus_3_db_and_14_seconds_is_retake_with_peak_high_and_too_long(tmp_path):
    wav = make_take(tmp_path / 'loud.wav', seconds=14, peak_db=-3)

    result = voice_check.check_take(wav, 'expert', TEXT, heard(TEXT))

    assert result['verdict'] == 'retake'
    assert {'peak_high', 'too_long'} <= set(result['reasons'])


def test_an_internal_pause_longer_than_a_second_is_a_pause(tmp_path):
    wav = make_take(tmp_path / 'pause.wav', pause=1.5)

    result = voice_check.check_take(wav, 'expert', TEXT, heard(TEXT))

    assert result['verdict'] == 'retake' and 'pause' in result['reasons']


def test_room_noise_at_the_start_is_noise(tmp_path):
    wav = make_take(tmp_path / 'noise.wav', noise_db=-40)

    result = voice_check.check_take(wav, 'expert', TEXT, heard(TEXT))

    assert 'noise' in result['reasons']


def test_a_different_transcript_is_a_text_problem(tmp_path):
    wav = make_take(tmp_path / 'text.wav')

    result = voice_check.check_take(wav, 'expert', TEXT, heard('Otra cosa completamente distinta.'))

    assert result['verdict'] == 'retake' and 'text' in result['reasons']


def test_without_whisper_the_check_notes_it_and_keeps_the_verdict(tmp_path):
    wav = make_take(tmp_path / 'nowhisper.wav')

    result = voice_check.check_take(wav, 'expert', TEXT, heard(None))

    assert result['verdict'] == 'ok' and 'whisper_missing' in result['notes']


def test_validate_needs_the_profile_and_the_take(refs):
    slug = profiles.create('Spec 010')
    params = {'profile': slug, 'style': 'expert', 'take': 1}

    assert voice_check.validate({'profile': 'nope', 'style': 'expert', 'take': 1}) == [
        {'code': 'unknown_profile', 'params': {'profile': 'nope'}}
    ]
    assert voice_check.validate(params) == [{'code': 'take_not_found', 'params': {'take': 1}}]
    assert voice_check.validate({**params, 'style': 'nope'}) == [{'code': 'unknown_style', 'params': {'style': 'nope'}}]

    profiles.takes_dir(slug, 'expert').mkdir(parents=True)
    (profiles.takes_dir(slug, 'expert') / '1.wav').write_bytes(b'RIFF')
    assert voice_check.validate(params) == []


def test_the_entry_point_writes_the_check_next_to_the_take(refs, monkeypatch, capsys):
    slug = profiles.create('Spec 010')
    profiles.takes_dir(slug, 'expert').mkdir(parents=True)
    make_take(profiles.takes_dir(slug, 'expert') / '1.wav')
    monkeypatch.setattr(voice_check.shutil, 'which', lambda name: None)  # sin whisper: el chequeo lo anota

    assert voice_check.main(['--profile', slug, '--style', 'expert', '--take', '1']) == 0

    written = json.loads((refs / slug / 'takes/expert/1.check.json').read_text(encoding='utf-8'))
    assert written['verdict'] == 'ok' and written['notes'] == ['whisper_missing']
    assert json.loads(capsys.readouterr().out)['verdict'] == 'ok'


def test_a_take_resampled_on_upload_says_so_in_its_check(refs, monkeypatch, capsys):
    slug = profiles.create('Spec 010')
    profiles.takes_dir(slug, 'expert').mkdir(parents=True)
    make_take(profiles.takes_dir(slug, 'expert') / '1.wav')
    monkeypatch.setattr(voice_check.shutil, 'which', lambda name: None)  # sin whisper, para no depender de él

    assert voice_check.main(['--profile', slug, '--style', 'expert', '--take', '1', '--source-rate', '44100']) == 0

    written = json.loads((refs / slug / 'takes/expert/1.check.json').read_text(encoding='utf-8'))
    assert written['notes'] == ['whisper_missing', 'resampled']
    assert written['measures']['source_rate'] == 44100


def test_the_check_runs_on_the_gpu_queue_and_names_the_take(tmp_path):
    command = voice_check.build_command({'profile': 'spec-010', 'style': 'expert', 'take': 2}, tmp_path)

    assert voice_check.RESOURCE == 'gpu'
    assert command[command.index('-m') + 1] == 'content_studio.services.voice_check'
    assert command[command.index('--take') + 1] == '2'
