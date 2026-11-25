"""Entrada de `subtitles.create` (spec 014, D-4): el documento de cada origen y el `subtitles.json` que deja `main`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_studio.clean import cuts as clean_cuts
from content_studio.diarization import speakers as diarization_speakers
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


def test_cleaner_words_drop_the_cuts_and_move_the_rest_to_the_clean_timeline(tmp_path):
    """AC-11: las palabras caen sobre el video limpio. Las de un corte se quitan; las demás pasan por `remap`."""
    analysis = tmp_path / 'analysis'
    analysis.mkdir()
    clean_cuts.save(analysis, {'cuts': [{'start': 1.0, 'end': 2.0, 'enabled': True}], 'duration': 4.0})
    words = [
        {'word': 'uno', 'start': 0.2, 'end': 0.6},
        {'word': 'dos', 'start': 1.2, 'end': 1.8},
        {'word': 'tres', 'start': 2.5, 'end': 3.0},
    ]

    kept = create_main.clean_words(words, analysis)

    assert [word['word'] for word in kept] == ['uno', 'tres']
    assert kept[0]['start'] == pytest.approx(0.2)
    assert kept[1]['start'] == pytest.approx(1.5)
    assert kept[1]['end'] == pytest.approx(2.0)


def test_main_writes_the_document_for_the_cleaner_origin_without_transcribing(tmp_path, capsys):
    """El origen del limpiador no transcribe: lee sus palabras y los cortes de SU análisis, deja `subtitles.json` y dice
    cuántos cues son. El transcript vive en la caché de transcripción, no junto a los cortes (AC-11)."""
    cache = tmp_path / 'cache'
    cache.mkdir()
    transcript = cache / 'transcript.json'
    transcript.write_text(json.dumps(WORDS), encoding='utf-8')
    analysis = tmp_path / 'analysis'
    analysis.mkdir()
    clean_cuts.save(analysis, {'cuts': [], 'duration': 1.0})
    folder = _job(
        tmp_path,
        {
            'origin': 'cleaner',
            'input': str(transcript),
            'analysis': str(analysis),
            'source': 'charla.mp4',
            'language': 'es',
        },
    )

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


def test_ac2_file_with_speakers_carries_each_cue_speaker_and_names():
    """AC-2: un origen de archivo con hablantes trae `speakers` con nombre y color, y `speaker` en cada cue."""
    names = {'SPEAKER_00': {'name': 'Ana', 'color': '#2563eb'}, 'SPEAKER_01': {'name': 'Luis', 'color': '#dc2626'}}
    words = [
        {'word': 'hola', 'start': 0.0, 'end': 0.4, 'speaker': 'SPEAKER_00'},
        {'word': 'mundo', 'start': 0.5, 'end': 0.9, 'speaker': 'SPEAKER_01'},
    ]

    doc = create_main.build_document('file', source='charla.wav', language='es', words=words, speakers=names)
    cleaner = create_main.build_document('cleaner', source='charla.mp4', language='es', words=words, speakers=names)

    assert doc['speakers'] == names
    assert [cue['speaker'] for cue in doc['cues']] == ['SPEAKER_00', 'SPEAKER_01']
    assert [cue['speaker'] for cue in cleaner['cues']] == ['SPEAKER_00', 'SPEAKER_01']


def test_ac2_words_take_the_speaker_of_their_turn():
    """AC-2: tag_speakers pone a cada palabra el hablante de su turno y arma los nombres como speakers.json."""
    result = {
        'exclusive_diarization': [
            {'start': 0.0, 'end': 0.6, 'speaker': 'SPEAKER_00'},
            {'start': 0.6, 'end': 1.0, 'speaker': 'SPEAKER_01'},
        ],
        'speakers': ['SPEAKER_00', 'SPEAKER_01'],
    }
    words = [{'word': 'hola', 'start': 0.0, 'end': 0.4}, {'word': 'mundo', 'start': 0.6, 'end': 0.9}]

    tagged, names = create_main.tag_speakers(words, result)

    assert [word['speaker'] for word in tagged] == ['SPEAKER_00', 'SPEAKER_01']
    assert names == diarization_speakers.build(['SPEAKER_00', 'SPEAKER_01'])


def test_ac2_cleaner_keeps_each_words_speaker(tmp_path):
    """AC-2: las palabras del limpiador conservan su hablante al pasar por los cortes."""
    analysis = tmp_path / 'analysis'
    analysis.mkdir()
    clean_cuts.save(analysis, {'cuts': [{'start': 1.0, 'end': 2.0, 'enabled': True}], 'duration': 4.0})
    words = [
        {'word': 'uno', 'start': 0.2, 'end': 0.6, 'speaker': 'SPEAKER_00'},
        {'word': 'tres', 'start': 2.5, 'end': 3.0, 'speaker': 'SPEAKER_01'},
    ]

    kept = create_main.clean_words(words, analysis)

    assert [(word['word'], word['speaker']) for word in kept] == [('uno', 'SPEAKER_00'), ('tres', 'SPEAKER_01')]
