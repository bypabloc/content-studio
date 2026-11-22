"""Servicio `subtitles.create` (spec 014, D-4): validación, comando y el documento que escribe `create_main`.

Lo que necesita GPU (transcribir un archivo o una narración) no se corre aquí: se prueba la parte pura y el origen
del limpiador y el importado, que no transcriben.
"""

from __future__ import annotations

import json
from pathlib import Path

from content_studio.services import subtitles_create
from content_studio.subtitles import create_main
from content_studio.subtitles.document import load


def _w(text: str, start: float, end: float) -> dict:
    return {'word': text, 'start': start, 'end': end}


WORDS = [_w('hola', 0.0, 0.4), _w('mundo', 0.5, 0.9), _w('buenas', 1.0, 1.4)]


def test_validate_rejects_an_import_that_is_not_srt_or_vtt():
    """Un .txt no es un SRT ni un VTT: el error es `unsupported_subtitle_format`. Un .SRT en mayúsculas pasa."""
    assert subtitles_create.validate({'origin': 'import', 'input': 'charla.txt'}) == [
        {'code': 'unsupported_subtitle_format', 'params': {'input': 'charla.txt'}}
    ]
    assert subtitles_create.validate({'origin': 'import', 'input': 'charla.SRT'}) == []


def test_validate_rejects_an_unknown_origin_and_a_missing_input():
    """Un origen que no existe o un archivo sin entrada son errores con su código."""
    assert {e['code'] for e in subtitles_create.validate({'origin': 'otro'})} == {'unknown_origin'}
    assert {e['code'] for e in subtitles_create.validate({'origin': 'file'})} == {'missing_input'}


def test_validate_asks_for_the_transcript_and_the_analysis_of_the_cleaner_and_the_script_of_a_narration():
    """El limpiador necesita su transcripción y la carpeta de sus cortes; la narración, el texto del guion."""
    assert {e['code'] for e in subtitles_create.validate({'origin': 'cleaner'})} == {
        'missing_transcript',
        'missing_analysis',
    }
    assert {e['code'] for e in subtitles_create.validate({'origin': 'narration', 'input': 'nota.wav'})} == {
        'missing_script'
    }


def test_validate_accepts_an_imported_file_without_a_model():
    """Importar un SRT no necesita modelo ni GPU: basta el archivo."""
    assert subtitles_create.validate({'origin': 'import', 'input': 'a.srt'}) == []


def test_build_command_runs_create_main_in_the_output_folder(tmp_path: Path):
    """El comando es el módulo `create_main` con la carpeta del trabajo, donde queda `subtitles.json`."""
    command = subtitles_create.build_command({'origin': 'import', 'input': 'a.srt'}, tmp_path)

    assert command[1:3] == ['-m', 'content_studio.subtitles.create_main']
    assert command[command.index('--folder') + 1] == str(tmp_path)


def test_build_document_from_the_cleaner_words_keeps_the_origin_kind():
    """Con las palabras del limpiador, el documento es del tipo «cleaner» y tiene sus cues."""
    doc = create_main.build_document('cleaner', source='clean.mp4', language='es', words=WORDS)

    assert doc['source'] == {'path': 'clean.mp4', 'kind': 'cleaner'}
    assert ' '.join(cue['text'] for cue in doc['cues']) == 'hola mundo buenas'


def test_build_document_from_an_imported_srt_reads_its_cues():
    """Con un SRT importado, el documento tiene los cues del archivo y el tipo «import»."""
    raw = '1\n00:00:00,000 --> 00:00:01,000\nHola\n'

    doc = create_main.build_document('import', source='a.srt', language='es', raw=raw)

    assert doc['source']['kind'] == 'import'
    assert [cue['text'] for cue in doc['cues']] == ['Hola']


def test_main_writes_subtitles_json_next_to_its_params(tmp_path: Path):
    """`create_main` lee `params.json` de su carpeta, arma el documento y lo guarda como `subtitles.json`."""
    transcript = tmp_path / 'transcript.json'
    transcript.write_text(json.dumps(WORDS), encoding='utf-8')
    create_main.clean_cuts.save(tmp_path, {'cuts': [], 'duration': 1.0})
    (tmp_path / 'params.json').write_text(
        json.dumps(
            {
                'origin': 'cleaner',
                'input': str(transcript),
                'analysis': str(tmp_path),
                'language': 'es',
                'source': 'clean.mp4',
            }
        ),
        encoding='utf-8',
    )

    assert create_main.main(['--folder', str(tmp_path)]) == 0

    doc = load(tmp_path / 'subtitles.json')
    assert doc['source']['kind'] == 'cleaner'
    assert ' '.join(cue['text'] for cue in doc['cues']) == 'hola mundo buenas'
