"""`tracks.json` de un trabajo de música (spec 011, D-6): una fila por pista, con su variante, duración y avisos."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from content_studio.music.manifest import write_manifest


def _tone(path: Path, seconds: float) -> Path:
    """Un tono de `seconds` s, con ffmpeg, para que la duración sea real."""
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=440:duration={seconds}',
            str(path),
        ],
        check=True,
    )
    return path


def _rows(folder: Path) -> list[dict]:
    return json.loads((folder / 'tracks.json').read_text(encoding='utf-8'))['tracks']


def test_manifest_lists_each_track_with_its_variant_duration_and_warning(tmp_path):
    long = _tone(tmp_path / 'acestep-lofi-chill-v1.wav', 3)
    short = _tone(tmp_path / 'acestep-corporate-v2.wav', 1)

    write_manifest(
        tmp_path,
        'acestep',
        3,
        [({'key': 'C Major', 'bpm': 80}, long), ({'key': 'G Major', 'bpm': 110}, short)],
        {long: False, short: True},
    )

    first, second = _rows(tmp_path)
    assert [first['file'], second['file']] == ['acestep-lofi-chill-v1.wav', 'acestep-corporate-v2.wav']
    assert (first['style'], first['variant'], first['warning'], first['voice']) == ('lofi-chill', 1, None, False)
    assert (second['style'], second['variant'], second['warning'], second['voice']) == (
        'corporate',
        2,
        'music_short',
        True,
    )
    assert (first['key'], first['bpm']) == ('C Major', 80)
    assert abs(first['duration'] - 3) < 0.05
    assert isinstance(first['lufs'], float)


def test_without_evaluation_the_voice_is_unknown(tmp_path):
    track = _tone(tmp_path / 'acestep-lofi-chill.wav', 1)

    write_manifest(tmp_path, 'acestep', 1, [({}, track)], {})

    row = _rows(tmp_path)[0]
    assert (row['voice'], row['variant'], row['key']) == (None, 1, None)
