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

from content_studio.clean import render as clean_render
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


# Las pruebas de abajo no ejecutan ffmpeg: miran los argumentos y el grafo que se le pasarían.


def _record(monkeypatch) -> list[tuple[str, ...]]:
    """Cambia `ffmpeg` por un registro de llamadas."""
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(ff, 'ffmpeg', lambda *args: calls.append(args) or '')
    return calls


def _graph(call: tuple[str, ...]) -> str:
    return call[call.index('-filter_complex') + 1]


def test_audio_is_pcm_24_in_wav_and_aac_in_the_rest():
    assert edit._audio_codec(Path('x.wav')) == ['-c:a', 'pcm_s24le']
    assert edit._audio_codec(Path('x.m4a')) == ['-c:a', 'aac', '-b:a', '192k']


def test_keep_on_a_video_fades_the_picture_and_the_sound(monkeypatch):
    calls = _record(monkeypatch)

    edit._keep(Path('in.mp4'), Path('out.mp4'), 1.0, 3.0, 0.5, 0.5, video=True)

    args = calls[0]
    assert args[args.index('-vf') + 1] == 'fade=t=in:st=0:d=0.5,fade=t=out:st=1.5:d=0.5'
    assert args[args.index('-af') + 1] == 'afade=t=in:st=0:d=0.5,afade=t=out:st=1.5:d=0.5'


def test_keep_on_a_video_without_fades_has_no_filters(monkeypatch):
    calls = _record(monkeypatch)

    edit._keep(Path('in.mp4'), Path('out.mp4'), 1.0, 3.0, 0.0, 0.0, video=True)

    assert '-vf' not in calls[0] and '-af' not in calls[0]


def test_trim_refuses_an_unknown_mode(tmp_path):
    with pytest.raises(ValueError, match='unknown trim mode'):
        edit.trim(tmp_path / 'a.wav', tmp_path / 'b.wav', start=0.0, end=1.0, mode='cut')


def test_audio_parts_are_relabelled_concatenated_or_joined_by_acrossfade():
    assert edit._audio_joins(1, 0.0) == ['[a0]anull[aout]']
    assert edit._audio_joins(2, 0.0) == ['[a0][a1]concat=n=2:v=0:a=1[aout]']
    assert edit._audio_joins(3, 0.5) == ['[a0][a1]acrossfade=d=0.5[x1]', '[x1][a2]acrossfade=d=0.5[aout]']


def test_video_fades_start_each_clip_before_the_previous_ends():
    """Cada `xfade` empieza `crossfade` antes del final acumulado: 3 s + 3 s con 1 s de fundido, offset de 2 s."""
    assert edit._video_joins([3.0, 3.0], 1.0) == ['[v0][v1]xfade=transition=fade:duration=1.0:offset=2.0[vout]']


def test_concatenating_audio_resamples_each_file_and_joins_them(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(edit, 'has_video', lambda path: False)

    edit.concat([tmp_path / 'a.wav', tmp_path / 'b.wav'], tmp_path / 'joined.wav')

    graph = _graph(calls[0])
    assert '[1:a]aresample=48000' in graph
    assert '[a0][a1]concat=n=2:v=0:a=1[aout]' in graph


def test_concatenating_videos_without_crossfade_joins_the_streams_directly(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(edit, 'has_video', lambda path: True)
    monkeypatch.setattr(ff, 'video_size', lambda path: (640, 360))
    monkeypatch.setattr(clean_render, 'frames_per_second', lambda path: 25)

    edit.concat([tmp_path / 'a.mp4', tmp_path / 'b.mp4'], tmp_path / 'joined.mp4')

    graph = _graph(calls[0])
    assert '[v0][a0][v1][a1]concat=n=2:v=1:a=1[vout][aout]' in graph
    assert 'scale=640:360' in graph
    assert calls[0][calls[0].index('-r') + 1] == '25'


def test_concatenating_videos_with_crossfade_uses_xfade_and_acrossfade(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(edit, 'has_video', lambda path: True)
    monkeypatch.setattr(ff, 'video_size', lambda path: (640, 360))
    monkeypatch.setattr(ff, 'probe_duration', lambda path: 3.0)
    monkeypatch.setattr(clean_render, 'frames_per_second', lambda path: 25)

    edit.concat([tmp_path / 'a.mp4', tmp_path / 'b.mp4'], tmp_path / 'joined.mp4', crossfade=1.0)

    graph = _graph(calls[0])
    assert '[v0][v1]xfade=transition=fade:duration=1.0:offset=2.0[vout]' in graph
    assert '[a0][a1]acrossfade=d=1.0[aout]' in graph


def test_split_without_exact_copies_the_streams(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(ff, 'probe_duration', lambda path: 20.0)

    parts = edit.split(tmp_path / 'long.wav', tmp_path / 'parts', 'long', every_seconds=10.0, exact=False)

    assert len(parts) == 2
    assert all(call[call.index('-c') + 1] == 'copy' for call in calls)


def test_split_needs_markers_or_a_length():
    with pytest.raises(ValueError, match='split needs markers or every_seconds'):
        edit._bounds(10.0, None, None)


def test_main_trims_through_its_subcommand(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(edit, 'has_video', lambda path: False)
    out = tmp_path / 'out' / 'kept.wav'

    code = edit.main(
        [
            'trim',
            '--input',
            str(tmp_path / 'in.wav'),
            '--out',
            str(out),
            '--start',
            '1',
            '--end',
            '2',
            '--fade-in',
            '0.2',
        ]
    )

    assert code == 0
    assert out.parent.is_dir()
    assert '-af' in calls[0]


def test_main_joins_with_a_crossfade_through_its_subcommand(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(edit, 'has_video', lambda path: False)

    code = edit.main(
        ['concat', '--input', 'a.wav', 'b.wav', '--out', str(tmp_path / 'out' / 'j.wav'), '--crossfade', '0.5']
    )

    assert code == 0
    assert 'acrossfade=d=0.5[aout]' in _graph(calls[0])


def test_main_splits_at_markers_through_its_subcommand(monkeypatch, tmp_path):
    calls = _record(monkeypatch)
    monkeypatch.setattr(ff, 'probe_duration', lambda path: 25.0)

    code = edit.main(
        [
            'split',
            '--input',
            'long.wav',
            '--out-dir',
            str(tmp_path / 'parts'),
            '--stem',
            'long',
            '--markers',
            '10',
            '20',
        ]
    )

    assert code == 0
    assert len(calls) == 3
