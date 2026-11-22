"""Entrada de `subtitles.create` (spec 014, D-4): el documento de cada origen y el `subtitles.json` que deja `main`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.subtitles import create_main
from content_studio.subtitles.document import load

WORDS = [
    {'word': 'hola', 'start': 0.0, 'end': 0.4},
    {'word': 'mundo', 'start': 0.5, 'end': 0.9},
]
SRT = '1\n00:00:00,000 --> 00:00:01,000\nhola mundo\n\n2\n00:00:01,500 --> 00:00:02,500\nbuenas\n'


def _job(tmp_path: Path, params: dict) -> Path:
    folder = tmp_path / 'job'
    folder.mkdir()
    (folder / 'params.json').write_text(json.dumps(params), encoding='utf-8')
    return folder


def test_build_document_gives_each_origin_its_cues():
    """El limpiador arma cues desde sus palabras y el importado, desde su SRT."""
    cleaner = create_main.build_document('cleaner', source='charla.mp4', language='es', words=WORDS)
    imported = create_main.build_document('import', source='charla.srt', language='es', raw=SRT)

    assert cleaner['cues']
    assert len(imported['cues']) == 2


def test_build_document_refuses_an_unknown_origin():
    """Un origen que no existe es un ValueError con el nombre en el mensaje."""
    with pytest.raises(ValueError, match='nope'):
        create_main.build_document('nope', source='x', language='es')


def test_words_from_transcript_reads_a_word_list_and_whisper_segments(tmp_path):
    """Un transcript del limpiador es una lista de palabras; uno de whisper las trae dentro de cada segmento."""
    cleaner_file = tmp_path / 'cleaner.json'
    cleaner_file.write_text(json.dumps(WORDS), encoding='utf-8')
    whisper_file = tmp_path / 'whisper.json'
    whisper_file.write_text(json.dumps({'segments': [{'words': WORDS}]}), encoding='utf-8')

    assert create_main._words_from_transcript(cleaner_file) == WORDS
    assert create_main._words_from_transcript(whisper_file) == WORDS


def test_main_writes_the_document_for_the_cleaner_origin_without_transcribing(tmp_path, capsys):
    """El origen del limpiador no transcribe: lee sus palabras, deja `subtitles.json` y dice cuántos cues son."""
    transcript = tmp_path / 'transcript.json'
    transcript.write_text(json.dumps(WORDS), encoding='utf-8')
    folder = _job(tmp_path, {'origin': 'cleaner', 'input': str(transcript), 'source': 'charla.mp4', 'language': 'es'})

    assert create_main.main(['--folder', str(folder)]) == 0

    doc = load(folder / 'subtitles.json')
    assert doc['cues']
    assert json.loads(capsys.readouterr().out) == {'cues': len(doc['cues'])}


def test_main_imports_an_srt_without_transcribing(tmp_path):
    """El origen importado lee el SRT de `input` y no pasa por whisper."""
    srt = tmp_path / 'charla.srt'
    srt.write_text(SRT, encoding='utf-8')
    folder = _job(tmp_path, {'origin': 'import', 'input': str(srt), 'source': 'charla.srt', 'language': 'es'})

    assert create_main.main(['--folder', str(folder)]) == 0

    assert len(load(folder / 'subtitles.json')['cues']) == 2


def test_main_transcribes_a_file_through_the_whisper_venv(tmp_path, monkeypatch):
    """`file` y `narration` transcriben: `main` activa el venv de whisper y toma las palabras de `_transcribe`."""
    used = {}
    monkeypatch.setattr(create_main.transcribe_main, '_venv', lambda: 'venv-whisper')
    monkeypatch.setattr(
        create_main.process,
        'use_venv',
        lambda venv, readme, module: used.update(venv=venv, module=module),
    )
    monkeypatch.setattr(create_main, '_transcribe', lambda source, model, language, folder: WORDS)
    folder = _job(
        tmp_path,
        {'origin': 'file', 'input': 'charla.wav', 'source': 'charla.mp4', 'language': 'es', 'model': 'tiny'},
    )

    assert create_main.main(['--folder', str(folder)]) == 0

    assert used == {'venv': 'venv-whisper', 'module': 'content_studio.subtitles.create_main'}
    assert load(folder / 'subtitles.json')['cues']


def test_transcribe_reuses_the_cached_words_without_running_ffmpeg(tmp_path, monkeypatch):
    """Con acierto de caché, `_transcribe` lee las palabras del json guardado y no corre ffmpeg ni whisper."""
    cached = tmp_path / 'cached.json'
    cached.write_text(json.dumps({'segments': [{'words': WORDS}]}), encoding='utf-8')
    source = tmp_path / 'charla.wav'
    source.write_bytes(b'RIFF')
    monkeypatch.setattr(create_main, 'connect', lambda path: None)
    monkeypatch.setattr(create_main.schema, 'migrate', lambda conn: None)
    monkeypatch.setattr(create_main.cache, 'find', lambda *args: str(cached))
    monkeypatch.setattr(create_main.ff, 'ffmpeg', lambda *args: pytest.fail('ffmpeg no debe correr con caché'))

    assert create_main._transcribe(source, model='tiny', language='es', folder=tmp_path) == WORDS


def test_transcribe_on_a_miss_extracts_the_audio_runs_whisper_and_stores_the_result(tmp_path, monkeypatch):
    """Sin caché: ffmpeg saca el audio, whisper escribe el json, la caché lo guarda y se devuelven las palabras."""
    source = tmp_path / 'charla.mp4'
    source.write_bytes(b'video')
    json_file = tmp_path / 'cache' / 'k.json'
    calls: dict = {}
    monkeypatch.setattr(create_main, 'connect', lambda path: None)
    monkeypatch.setattr(create_main.schema, 'migrate', lambda conn: None)
    monkeypatch.setattr(create_main.cache, 'find', lambda *args: None)
    monkeypatch.setattr(create_main.cache, 'cache_key', lambda *args: 'k')
    monkeypatch.setattr(create_main.cache, 'json_path', lambda key: json_file)
    monkeypatch.setattr(create_main.ff, 'ffmpeg', lambda *args: calls.update(ffmpeg=args))
    monkeypatch.setattr(create_main.transcribe_main, '_load_model', lambda name: f'model:{name}')
    monkeypatch.setattr(create_main.cache, 'store', lambda conn, *args: calls.update(stored=args[-1]))

    def fake_transcribe(wav, *, language, out, model):
        calls.update(language=language, model=model)
        out.write_text(json.dumps({'segments': [{'words': WORDS}]}), encoding='utf-8')

    monkeypatch.setattr(create_main.transcribe_main, 'transcribe', fake_transcribe)

    assert create_main._transcribe(source, model='tiny', language='es', folder=tmp_path) == WORDS
    assert calls['ffmpeg'][0] == '-y'
    assert calls['language'] == 'es'
    assert calls['model'] == 'model:tiny'
    assert calls['stored'] == str(json_file)
