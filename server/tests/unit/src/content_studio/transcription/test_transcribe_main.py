"""Transcripción en `.venv-whisper` (spec 013, D-2): el JSON de palabras y el progreso, sin faster-whisper."""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from content_studio.common import ffmpeg as ff
from content_studio.common import process
from content_studio.transcription import transcribe_main


def _word(start: float, end: float, word: str) -> SimpleNamespace:
    return SimpleNamespace(start=start, end=end, word=word, probability=0.9)


def _segment(start: float, end: float, text: str, words: list) -> SimpleNamespace:
    return SimpleNamespace(start=start, end=end, text=text, words=words)


class FakeModel:
    """Imita WhisperModel.transcribe: un generador de segmentos y la info de la transcripción."""

    def __init__(self, segments: list, info: SimpleNamespace) -> None:
        self._segments = segments
        self._info = info
        self.calls: list[dict] = []

    def transcribe(self, audio: str, **options) -> tuple:
        self.calls.append({'audio': audio, **options})
        return iter(self._segments), self._info


def test_the_words_payload_keeps_language_duration_and_word_times():
    """El JSON trae el idioma, su probabilidad, la duración y cada palabra con sus tiempos."""
    segments = [_segment(0.0, 1.0, ' hola mundo', [_word(0.0, 0.4, 'hola'), _word(0.5, 1.0, 'mundo')])]
    info = SimpleNamespace(language='es', language_probability=0.98, duration=1.0)

    payload = transcribe_main.words_payload(segments, info)

    assert payload['language'] == 'es'
    assert payload['language_probability'] == 0.98
    assert payload['duration'] == 1.0
    assert payload['segments'][0]['text'] == 'hola mundo'
    assert payload['segments'][0]['words'][1] == {'start': 0.5, 'end': 1.0, 'word': 'mundo', 'probability': 0.9}


def test_progress_is_the_end_of_the_segment_over_the_duration():
    """El progreso es el fin del último segmento dividido por la duración del audio."""
    assert transcribe_main.progress_fraction(end=2.5, duration=10.0) == 0.25
    assert transcribe_main.progress_fraction(end=12.0, duration=10.0) == 1.0
    assert transcribe_main.progress_fraction(end=1.0, duration=0.0) == 0.0


def test_transcribe_writes_the_words_json_with_the_model_options(tmp_path):
    """Con un modelo (falso) transcribe el audio con word_timestamps y VAD, y escribe el JSON en `out`."""
    segments = [_segment(0.0, 2.0, 'buenas', [_word(0.0, 2.0, 'buenas')])]
    info = SimpleNamespace(language='es', language_probability=0.99, duration=2.0)
    model = FakeModel(segments, info)
    out = tmp_path / 'words.json'

    transcribe_main.transcribe(tmp_path / 'audio.wav', language='es', out=out, model=model)

    assert model.calls == [
        {'audio': str(tmp_path / 'audio.wav'), 'language': 'es', 'word_timestamps': True, 'vad_filter': True}
    ]
    written = json.loads(out.read_text(encoding='utf-8'))
    assert written['segments'][0]['words'][0]['word'] == 'buenas'


def test_auto_language_passes_no_language_to_the_model(tmp_path):
    """Con idioma «auto», el modelo detecta el idioma (language=None)."""
    info = SimpleNamespace(language='en', language_probability=0.95, duration=1.0)
    model = FakeModel([], info)

    transcribe_main.transcribe(tmp_path / 'a.wav', language='auto', out=tmp_path / 'w.json', model=model)

    assert model.calls[0]['language'] is None


def test_the_parser_takes_input_model_language_and_out():
    """Los flags del servicio: --input, --model, --language y --out."""
    args = transcribe_main.build_parser().parse_args(
        ['--input', 'v.mp4', '--model', 'small', '--language', 'es', '--out', 'w.json']
    )

    assert (args.input, args.model, args.language, args.out) == ('v.mp4', 'small', 'es', 'w.json')


@pytest.mark.local
def test_transcribes_three_seconds_with_small_in_the_whisper_venv(tmp_path):
    """Real (solo en este equipo): el servicio corre en `.venv-whisper` y devuelve el JSON de 3 s con `small`."""
    audio = tmp_path / 'tono.wav'
    ff.ffmpeg('-y', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=3', '-ac', '1', '-ar', '16000', str(audio))
    out = tmp_path / 'words.json'
    venv = transcribe_main._venv()

    subprocess.run(
        [
            str(process.python_de(venv)), '-m', 'content_studio.transcription.transcribe_main',
            '--input', str(audio), '--model', 'small', '--language', 'es', '--out', str(out),
        ],
        check=True,
        env=process.env_src(),
    )  # fmt: skip

    payload = json.loads(out.read_text(encoding='utf-8'))
    assert abs(payload['duration'] - 3.0) < 0.1
    assert isinstance(payload['segments'], list)
