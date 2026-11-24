"""Tomas de un perfil (spec 010, D-3 y AC-5): se guardan numeradas y elegir una la copia a la referencia del estilo."""

from __future__ import annotations

import io
import wave

import pytest
import soundfile as sf

from content_studio import paths
from content_studio.narration import profile_takes, profiles, recording_kit


@pytest.fixture
def refs(tmp_path, monkeypatch):
    """Una carpeta de referencias vacía en lugar de server/data/narration/reference/."""
    root = tmp_path / 'reference'
    root.mkdir()
    monkeypatch.setattr(paths, 'REFERENCE', root)
    return root


def test_ac5_choosing_take_2_copies_it_and_the_previous_choice_stays_in_takes(refs):
    slug = profiles.create('Spec 010')
    (refs / slug / 'expert.wav').write_bytes(b'VIEJA')
    assert profile_takes.save_take(slug, 'expert', b'UNO') == 1
    assert profile_takes.save_take(slug, 'expert', b'DOS') == 2

    profile_takes.choose(slug, 'expert', 2)

    assert (refs / slug / 'expert.wav').read_bytes() == b'DOS'
    assert (refs / slug / 'takes/expert/2.wav').read_bytes() == b'DOS'  # la toma se copia, no se mueve
    assert b'VIEJA' in [p.read_bytes() for p in (refs / slug / 'takes/expert').glob('*.wav')]


def test_choose_writes_the_script_as_the_transcript_next_to_the_wav(refs):
    slug = profiles.create('Spec 010')
    profile_takes.save_take(slug, 'expert', b'UNO')

    profile_takes.choose(slug, 'expert', 1)

    assert (refs / slug / 'expert.txt').read_text(encoding='utf-8') == recording_kit.plain_text('expert')


def test_takes_are_numbered_per_style(refs):
    slug = profiles.create('Spec 010')

    assert profile_takes.save_take(slug, 'expert', b'A') == 1
    assert profile_takes.save_take(slug, 'expert', b'B') == 2
    assert profile_takes.save_take(slug, 'clear', b'C') == 1
    assert profile_takes.list_takes(slug, 'expert') == [1, 2]


def test_choosing_a_missing_take_is_an_error(refs):
    slug = profiles.create('Spec 010')

    with pytest.raises(profile_takes.TakeNotFound):
        profile_takes.choose(slug, 'expert', 9)


def test_only_kit_styles_can_have_takes(refs):
    slug = profiles.create('Spec 010')

    with pytest.raises(ValueError):
        profile_takes.save_take(slug, 'nope', b'x')


def _wav(rate: int) -> bytes:
    """Medio segundo de silencio en un WAV mono de 16 bits a `rate`: lo que sube un micrófono que no da 48 kHz."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(b'\x00\x00' * (rate // 2))
    return buffer.getvalue()


def test_a_take_from_a_44100_microphone_is_resampled_to_48k_and_keeps_its_source_rate():
    out, source = profile_takes.to_48k(_wav(44100))

    assert source == 44100
    info = sf.info(io.BytesIO(out))  # soundfile lee el WAV de 24 bits que escribe ffmpeg (formato extensible)
    assert info.samplerate == 48000
    assert abs(info.frames - 24000) < 100  # medio segundo sigue siendo medio segundo


def test_a_take_already_at_48k_is_kept_as_it_is():
    data = _wav(48000)

    assert profile_takes.to_48k(data) == (data, None)
