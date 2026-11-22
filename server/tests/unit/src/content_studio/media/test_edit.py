"""AC-7, AC-8 y AC-9 (spec 015, D-5, T6): recortar (`keep` con fundidos, `remove` con los tramos unidos), unir (con
crossfade, y `mixed_kinds` para audio con video) y dividir (cada N segundos o en marcadores). Los medios son fixtures
generadas aquí con ffmpeg; sin ffmpeg, las pruebas que lo usan se saltan."""

from __future__ import annotations

import array
import math
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.common import ffmpeg as ff
from content_studio.media import edit

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def _ffmpeg(*args: str) -> None:
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', *args], check=True)


def _noise(path: Path, seconds: float) -> Path:
    """Ruido rosa mono de 48 kHz: suena parecido a voz y no tiene un nivel plano que confunda la medición."""
    _ffmpeg(
        '-f',
        'lavfi',
        '-i',
        f'anoisesrc=color=pink:duration={seconds}:amplitude=0.5:seed=7',
        '-c:a',
        'pcm_s24le',
        str(path),
    )
    return path


def _video(path: Path, seconds: float, size: str) -> Path:
    """Un video de `size` a 25 cuadros por segundo, con audio de ruido rosa."""
    _ffmpeg(
        '-f', 'lavfi', '-i', f'testsrc2=size={size}:rate=25:duration={seconds}',
        '-f', 'lavfi', '-i', f'anoisesrc=color=pink:duration={seconds}:amplitude=0.5:seed=3',
        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(path),
    )  # fmt: skip
    return path


def _rms(path: Path, start: float, end: float) -> float:
    """El RMS (0 a 1) del audio de `path` entre `start` y `end` segundos."""
    raw = subprocess.run(
        [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-i',
            str(path),
            '-f',
            's16le',
            '-ac',
            '1',
            '-ar',
            '48000',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout
    samples = array.array('h')
    samples.frombytes(raw)
    window = samples[int(start * 48000) : int(end * 48000)]
    return math.sqrt(sum(s * s for s in window) / len(window)) / 32768 if window else 0.0


def test_the_fade_filters_fade_in_from_zero_and_out_before_the_end():
    """Los fundidos caen dentro del tramo: entrada desde 0 y salida terminando en la duración."""
    assert edit.fade_filters('afade', 10.0, 0.5, 0.0) == 'afade=t=in:st=0:d=0.5'
    assert edit.fade_filters('afade', 10.0, 0.0, 0.5) == 'afade=t=out:st=9.5:d=0.5'
    assert edit.fade_filters('fade', 10.0, 0.0, 0.0) == ''


@needs_ffmpeg
def test_ac7_remove_takes_two_to_four_seconds_out_of_ten(tmp_path):
    """AC-7: quitar 2–4 s de un audio de 10 s deja 8 s, ±20 ms."""
    source = _noise(tmp_path / 'source.wav', 10)
    out = tmp_path / 'cut.wav'

    edit.trim(source, out, start=2.0, end=4.0, mode='remove')

    assert abs(ff.probe_duration(out) - 8.0) <= 0.02


@needs_ffmpeg
def test_ac7_keep_with_half_a_second_fade_in_is_20_db_quieter_at_the_start(tmp_path):
    """AC-7: en `keep` con fundido de entrada de 0,5 s, el RMS de los primeros 50 ms es al menos 20 dB menor que el
    del segundo 1."""
    source = _noise(tmp_path / 'source.wav', 10)
    out = tmp_path / 'kept.wav'

    edit.trim(source, out, start=2.0, end=8.0, mode='keep', fade_in=0.5)

    assert _rms(out, 0.0, 0.05) <= _rms(out, 1.0, 2.0) / 10  # 20 dB son un factor de 10 en el RMS


@needs_ffmpeg
def test_remove_on_a_video_keeps_its_size_and_drops_the_span(tmp_path):
    """Quitar un tramo de un video deja su resolución y la duración menos el tramo."""
    source = _video(tmp_path / 'clip.mp4', 4, '320x240')
    out = tmp_path / 'cut.mp4'

    edit.trim(source, out, start=1.0, end=3.0, mode='remove')

    assert ff.video_size(out) == (320, 240)
    assert abs(ff.probe_duration(out) - 2.0) <= 0.05


@needs_ffmpeg
def test_ac8_three_videos_of_different_sizes_keep_the_first_size_and_lose_two_seconds(tmp_path):
    """AC-8: unir 3 videos de resoluciones distintas con crossfade de 1 s da la resolución del primero y dura la suma
    menos 2 s, ±1 cuadro (0,04 s a 25 fps)."""
    clips = [
        _video(tmp_path / 'a.mp4', 3, '640x360'),
        _video(tmp_path / 'b.mp4', 3, '320x240'),
        _video(tmp_path / 'c.mp4', 3, '854x480'),
    ]
    out = tmp_path / 'joined.mp4'

    edit.concat(clips, out, crossfade=1.0)

    assert ff.video_size(out) == (640, 360)
    assert abs(ff.probe_duration(out) - 7.0) <= 0.04


@needs_ffmpeg
def test_ac8_joining_audio_with_video_is_refused_as_mixed_kinds(tmp_path):
    """AC-8: unir audio con video da `mixed_kinds`."""
    audio = _noise(tmp_path / 'voice.wav', 2)
    video = _video(tmp_path / 'clip.mp4', 2, '320x240')

    with pytest.raises(ValueError, match='mixed_kinds'):
        edit.concat([audio, video], tmp_path / 'joined.mp4')


@needs_ffmpeg
def test_ac9_splitting_25_minutes_every_10_minutes_gives_10_10_and_5(tmp_path):
    """AC-9: un audio de 25 min dividido cada 10 min da 3 partes de 10, 10 y 5 min, ±20 ms."""
    source = tmp_path / 'long.wav'
    _ffmpeg('-f', 'lavfi', '-i', 'anullsrc=r=8000:cl=mono:d=1500', '-c:a', 'pcm_s16le', str(source))

    parts = edit.split(source, tmp_path / 'parts', 'long', every_seconds=600)

    assert len(parts) == 3
    for part, expected in zip(parts, (600.0, 600.0, 300.0), strict=True):
        assert abs(ff.probe_duration(part) - expected) <= 0.02


@needs_ffmpeg
def test_ac9_markers_at_60_and_120_seconds_make_three_parts(tmp_path):
    """AC-9: con los marcadores [60, 120] salen 3 partes: 60 s, 60 s y el resto."""
    source = tmp_path / 'long.wav'
    _ffmpeg('-f', 'lavfi', '-i', 'anullsrc=r=8000:cl=mono:d=1500', '-c:a', 'pcm_s16le', str(source))

    parts = edit.split(source, tmp_path / 'parts', 'long', markers=[60, 120])

    assert len(parts) == 3
    assert abs(ff.probe_duration(parts[0]) - 60.0) <= 0.02
    assert abs(ff.probe_duration(parts[2]) - 1380.0) <= 0.02
