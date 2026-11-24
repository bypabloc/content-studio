"""Exportaciones del limpiador: transcripción, SRT, EDL, XML e informe (spec 013, AC-5)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from content_studio.clean import exports
from content_studio.clean.plan import Cut

FIXTURES = Path(__file__).parent / 'fixtures'

# AC-1: huecos de 0.55 s y 1.4 s de voz, con el final de 0.15 s; duración original 3.5 s.
KEEP = [(0.0, 0.55), (1.05, 2.45), (3.35, 3.5)]
CUTS: list[Cut] = [
    {'start': 0.55, 'end': 1.05, 'enabled': True},
    {'start': 2.45, 'end': 3.35, 'enabled': True},
]
WORDS = [
    {'start': 0.0, 'end': 0.4, 'word': 'hola'},
    {'start': 1.2, 'end': 1.6, 'word': 'mundo'},
    {'start': 1.9, 'end': 2.3, 'word': 'buenas'},
]


def test_ac5_edl_is_cmx3600_with_one_event_per_segment_summing_the_duration():
    """AC-5: el EDL es CMX3600, un evento por tramo; el último cierra en la duración limpia (2.1 s, 2 s 3 cuadros)."""
    text = exports.edl(KEEP, fps=25)

    assert text.splitlines()[0].startswith('TITLE:')
    assert 'FCM: NON-DROP FRAME' in text
    events = [line.split() for line in text.splitlines() if re.match(r'^\d{3}\s', line)]
    assert len(events) == 3
    assert events[0][-4:] == ['00:00:00:00', '00:00:00:14', '00:00:00:00', '00:00:00:14']
    assert events[-1][-1] == '00:00:02:03'


def test_ac5_xml_is_xmeml_with_one_clipitem_per_segment():
    """AC-5: el XML es xmeml v5 con sequence/media/video/track/clipitem, uno por tramo, sobre el archivo original."""
    text = exports.xml_sequence(KEEP, fps=25, media_path='/media/entrada.mp4', name='limpio', duration=3.5)

    root = ET.fromstring(text)
    assert root.tag == 'xmeml'
    assert root.get('version') == '5'
    clips = root.findall('./sequence/media/video/track/clipitem')
    assert len(clips) == 3
    assert clips[0].findtext('in') == '0'
    assert clips[0].find('file/pathurl') is not None


def test_ac5_srt_has_no_line_longer_than_42_characters_and_at_most_two_lines():
    """AC-5: ningún renglón del SRT pasa de 42 caracteres y cada bloque tiene como mucho 2 renglones."""
    words = [{'start': i * 0.3, 'end': i * 0.3 + 0.25, 'word': f'word{i:02d}'} for i in range(60)]

    text = exports.srt(words, cuts=[])

    blocks = [b for b in text.strip().split('\n\n') if b]
    assert blocks
    for block in blocks:
        lines = block.splitlines()[2:]
        assert 1 <= len(lines) <= 2
        assert all(len(line) <= 42 for line in lines)


def test_ac5_report_has_the_right_figures():
    """AC-5: el informe reúne duración antes y después, lo cortado, la cantidad de cortes y el modelo."""
    report = exports.report(
        duration_before=3.5, keep=KEEP, cuts=CUTS, model='large-v3-turbo', language='es', process_seconds=12.3456
    )

    assert report['duration_before'] == 3.5
    assert report['duration_after'] == 2.1
    assert report['removed_seconds'] == 1.4
    assert report['removed_percent'] == 40.0
    assert report['cuts'] == 2
    assert report['model'] == 'large-v3-turbo'
    assert report['language'] == 'es'
    assert report['process_seconds'] == 12.35


def test_transcript_txt_joins_the_segment_texts_one_per_line():
    """La transcripción en texto tiene un renglón por segmento."""
    segments = [{'start': 0.0, 'end': 1.0, 'text': 'Hola mundo'}, {'start': 1.0, 'end': 2.0, 'text': 'Adiós'}]

    assert exports.transcript_txt(segments) == 'Hola mundo\nAdiós\n'


def test_transcript_json_keeps_words_with_remapped_times():
    """El JSON de la transcripción conserva cada palabra con sus tiempos reasignados al limpio."""
    result = exports.transcript_json(WORDS, CUTS)

    assert [w['word'] for w in result] == ['hola', 'mundo', 'buenas']
    assert [(round(w['start'], 6), round(w['end'], 6)) for w in result] == [(0.0, 0.4), (0.7, 1.1), (1.4, 1.8)]


def test_ac5_golden_edl_matches_the_fixture():
    """El EDL del AC-1 sale igual al golden file."""
    assert exports.edl(KEEP, fps=25) == (FIXTURES / 'cuts_ac1.edl').read_text(encoding='utf-8')


def test_ac5_golden_srt_matches_the_fixture():
    """Los subtítulos de doce palabras salen igual al golden file: un bloque de dos renglones."""
    words = [{'start': i * 0.3, 'end': i * 0.3 + 0.25, 'word': f'word{i:02d}'} for i in range(12)]

    assert exports.srt(words, cuts=[]) == (FIXTURES / 'srt_sample.srt').read_text(encoding='utf-8')
