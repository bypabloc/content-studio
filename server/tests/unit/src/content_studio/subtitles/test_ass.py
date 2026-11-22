"""Generación de ASS (spec 014, D-3, AC-3): un Dialogue por palabra activa en redes y por cue en clásico."""

from __future__ import annotations

import subprocess
from pathlib import Path

from content_studio.subtitles.ass import to_ass
from content_studio.subtitles.document import new_document
from content_studio.subtitles.styles import preset

# cspell:ignore centiseconds: unidad de tiempo de ASS en las pruebas.
# Highlight `#FFD400` en ASS (BGR): &H00D4FF&.
HIGHLIGHT = '\\c&H00D4FF&'
POP = '\\t(0,80,\\fscx115\\fscy115)\\t(80,160,\\fscx100\\fscy100)'


def _doc() -> dict:
    words = [
        {'start': 0.0, 'end': 0.5, 'text': 'hola'},
        {'start': 0.5, 'end': 1.0, 'text': 'mundo'},
        {'start': 1.0, 'end': 1.5, 'text': 'buenas'},
    ]
    cue = {'id': 1, 'start': 0.0, 'end': 1.5, 'text': 'hola mundo buenas', 'words': words}
    return new_document(source_path='entrada.wav', kind='file', language='es', cues=[cue])


def _dialogues(ass: str) -> list[str]:
    return [line for line in ass.splitlines() if line.startswith('Dialogue:')]


def test_ac3_reels_writes_one_dialogue_per_active_word_in_highlight_uppercase_with_pop():
    """AC-3: con reels hay un Dialogue por palabra activa, con esa palabra en el color de resaltado, en mayúsculas y
    con el pop."""
    ass = to_ass(_doc(), preset('reels'), play_res=(1080, 1920))

    lines = _dialogues(ass)
    assert len(lines) == 3
    assert all(HIGHLIGHT in line for line in lines)
    assert all(POP in line for line in lines)
    assert 'HOLA' in lines[0]
    assert 'MUNDO' in lines[1]
    assert 'BUENAS' in lines[2]
    assert 'Dialogue: 0,0:00:00.00,0:00:00.50,' in lines[0]


def test_ac3_classic_writes_one_dialogue_per_cue():
    """AC-3: con classic hay un Dialogue por cue, con el texto del cue tal cual."""
    lines = _dialogues(to_ass(_doc(), preset('classic'), play_res=(1920, 1080)))

    assert len(lines) == 1
    assert 'hola mundo buenas' in lines[0]


def test_ac3_play_res_follows_the_video_resolution():
    """PlayResX y PlayResY son la resolución del video."""
    ass = to_ass(_doc(), preset('reels'), play_res=(1080, 1920))

    assert 'PlayResX: 1080' in ass
    assert 'PlayResY: 1920' in ass


def test_karaoke_writes_a_kf_tag_per_word_in_centiseconds():
    """El karaoke marca cada palabra con \\kf en centésimas de segundo (0,5 s = 50)."""
    ass = to_ass(_doc(), preset('karaoke'), play_res=(1920, 1080))

    assert ass.count('\\kf50') == 3


def test_ac3_the_generated_ass_is_accepted_by_ffmpeg(tmp_path: Path):
    """AC-3: ffmpeg lee el ASS y lo reescribe con todos sus Dialogue. (`-f null` no sirve para subtítulos: no hay
    stream que mapear; por eso se usa `-c:s ass -f ass -`.)"""
    path = tmp_path / 'x.ass'
    ass = to_ass(_doc(), preset('reels'), play_res=(1080, 1920))
    path.write_text(ass, encoding='utf-8')

    result = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-c:s', 'ass', '-f', 'ass', '-'],
        check=True,
        capture_output=True,
    )

    assert result.stdout.decode('utf-8').count('Dialogue:') == ass.count('Dialogue:') == 3
