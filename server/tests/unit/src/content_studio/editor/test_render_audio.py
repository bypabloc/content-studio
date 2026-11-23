"""Render de audio del editor (spec 017, D-4, AC-4 y AC-5): el grafo `filter_complex` y el archivo que sale."""

from __future__ import annotations

import array
import cmath
import math
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

# cspell:ignore frombytes: método de array de la biblioteca estándar.
from content_studio.common.ffmpeg import probe_duration
from content_studio.editor import render_audio

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
GOLDEN = Path(__file__).resolve().parents[4] / 'fixtures' / 'editor' / 'graph-basico.filter'


def _track(track_id: str, **flags) -> dict:
    base = {'id': track_id, 'kind': 'audio', 'name': track_id, 'volume_db': 0, 'mute': False, 'solo': False}
    return {**base, 'locked': False, 'height': 80, **flags}


def _clip(clip_id: str, track: str, src: str, start: float, length: float, **extra) -> dict:
    base = {'id': clip_id, 'track': track, 'src': src, 'src_in': 0.0, 'src_out': length, 'start': start}
    return {**base, 'gain_db': 0, 'fade_in': 0, 'fade_out': 0, **extra}


def _doc(tracks: list, clips: list) -> dict:
    return {'version': 1, 'name': 'demo', 'sample_rate': 48000, 'tracks': tracks, 'clips': clips, 'markers': []}


def test_the_graph_matches_the_golden(tmp_path):
    """AC-4: dos pistas con fundidos y volúmenes dan el grafo de `fixtures/editor/graph-basico.filter`."""
    doc = _doc(
        [_track('t1'), _track('t2', volume_db=-3)],
        [
            _clip('c1', 't1', 'media/voz.wav', 0, 4, fade_in=0.5, fade_out=1),
            _clip('c2', 't2', 'media/musica.wav', 2, 6, gain_db=-6),
        ],
    )

    plan = render_audio.build(doc, tmp_path)

    assert plan.script == GOLDEN.read_text(encoding='utf-8')


def test_muted_tracks_are_left_out_and_solo_keeps_only_the_soloed_track(tmp_path):
    """Una pista silenciada no entra en el grafo; si alguna está en solo, solo entran las que lo tienen."""
    doc = _doc(
        [_track('t1', mute=True), _track('t2'), _track('t3')],
        [_clip('c1', 't1', 'a.wav', 0, 2), _clip('c2', 't2', 'b.wav', 0, 2), _clip('c3', 't3', 'c.wav', 0, 2)],
    )
    assert [path.name for path in render_audio.build(doc, tmp_path).inputs] == ['b.wav', 'c.wav']

    soloed = _doc(
        [_track('t1'), _track('t2', solo=True)],
        [_clip('c1', 't1', 'a.wav', 0, 2), _clip('c2', 't2', 'b.wav', 0, 2)],
    )
    assert [path.name for path in render_audio.build(soloed, tmp_path).inputs] == ['b.wav']


def test_a_project_without_active_clips_cannot_render(tmp_path):
    """Un proyecto sin clips que suenen no se renderiza: `nothing_to_render`."""
    with pytest.raises(render_audio.RenderError) as caught:
        render_audio.build(_doc([_track('t1')], []), tmp_path)

    assert caught.value.code == 'nothing_to_render'


def test_audio_render_ignores_visual_tracks_and_clips(tmp_path):
    """El render de audio solo lee clips de audio dentro de un proyecto mixto v2."""
    video_track = {'id': 'v1', 'kind': 'video', 'name': 'Video', 'opacity': 1, 'hidden': False, 'locked': False}
    visual_clip = {
        'id': 'picture',
        'track': 'v1',
        'src': 'missing.mp4',
        'src_in': 0,
        'src_out': 2,
        'start': 0,
        'fade_in': 0,
        'fade_out': 0,
        'media': 'video',
        'transform': {},
        'keyframes': {},
    }
    doc = _doc([_track('audio'), video_track], [_clip('voice', 'audio', 'voice.wav', 0, 2), visual_clip])
    doc.update(version=2, canvas={'width': 1920, 'height': 1080, 'fps': 30, 'background': '#000000'}, transitions=[])

    plan = render_audio.build(doc, tmp_path)

    assert [path.name for path in plan.inputs] == ['voice.wav']
    assert render_audio._missing_sources({'clips': [visual_clip]}, tmp_path) == []


def test_a_marker_segment_keeps_only_its_source_range_and_resets_the_timeline(tmp_path):
    """Un tramo entre marcadores empieza en cero y recorta el rango de fuente de cada clip."""
    doc = _doc([_track('t1')], [_clip('c1', 't1', 'media/a.wav', 1, 8)])

    plan = render_audio.build(doc, tmp_path, start=2, end=5)

    assert plan.script == (
        '[0:a]atrim=start=1:end=4,asetpts=PTS-STARTPTS,aresample=48000,'
        'aformat=sample_fmts=fltp:channel_layouts=stereo,volume=0dB,adelay=0:all=1[c0];\n'
        '[c0]amix=inputs=1:normalize=0:dropout_transition=0[mix];\n'
        '[mix]apad=whole_dur=3,atrim=end=3[out]\n'
    )


def test_speed_scales_partial_source_ranges_and_keeps_pitch_in_the_graph(tmp_path):
    """AC-4: el rango de fuente se escala por velocidad y la cadena conserva el tono."""
    doc = _doc(
        [_track('audio')],
        [_clip('voice', 'audio', 'voice.wav', 0, 4, src_in=1, src_out=5, speed=2)],
    )
    doc['version'] = 3

    plan = render_audio.build(doc, tmp_path, start=0.5, end=1.5)

    assert 'atrim=start=2:end=4' in plan.script
    assert 'atempo=2' in plan.script


def test_a_missing_source_fails_with_the_paths_in_the_error(tmp_path):
    """AC-10: exportar con una fuente ausente devuelve `missing_source` y sus rutas."""
    doc = _doc([_track('t1')], [_clip('c1', 't1', 'missing.wav', 0, 2)])

    with pytest.raises(render_audio.RenderError) as caught:
        render_audio.render(doc, tmp_path, tmp_path / 'output.wav')

    assert caught.value.code == 'missing_source'
    assert caught.value.params == {'paths': ['missing.wav']}


@needs_ffmpeg
def test_the_wav_lasts_as_long_as_the_project(tmp_path):
    """AC-4: la salida dura lo que el proyecto: 1 s de inicio y 2 s de clip, 3 s."""
    media = tmp_path / 'media'
    media.mkdir()
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=1000:duration=5:sample_rate=48000',
            str(media / 'tono.wav'),
        ],
        check=True,
    )
    doc = _doc([_track('t1')], [_clip('c1', 't1', 'media/tono.wav', 1, 2)])
    out = tmp_path / 'salida.wav'

    render_audio.render(doc, tmp_path, out, format='wav')

    assert probe_duration(out) == pytest.approx(3, abs=0.01)


def _fft(values: list[float]) -> list[complex]:
    """FFT iterativo de radix 2 para medir el tono sin dependencias de prueba."""
    size = len(values)
    result = [complex(value) for value in values]
    reversed_index = 0
    for index in range(1, size):
        bit = size >> 1
        while reversed_index & bit:
            reversed_index ^= bit
            bit >>= 1
        reversed_index ^= bit
        if index < reversed_index:
            result[index], result[reversed_index] = result[reversed_index], result[index]
    width = 2
    while width <= size:
        half = width // 2
        step = cmath.exp(-2j * math.pi / width)
        for start in range(0, size, width):
            factor = 1 + 0j
            for offset in range(half):
                even = result[start + offset]
                odd = factor * result[start + offset + half]
                result[start + offset] = even + odd
                result[start + offset + half] = even - odd
                factor *= step
        width *= 2
    return result


def _dominant_frequency(path: Path) -> float:
    """Devuelve el pico FFT de una ventana mono de 8192 muestras."""
    size = 8192
    with wave.open(str(path), 'rb') as audio:
        rate, channels = audio.getframerate(), audio.getnchannels()
        audio.setpos(int(rate * 0.25))
        frames = array.array('h')
        frames.frombytes(audio.readframes(size))
    samples = [float(frames[index * channels]) for index in range(size)]
    windowed = [
        sample * (0.5 - 0.5 * math.cos(2 * math.pi * index / (size - 1))) for index, sample in enumerate(samples)
    ]
    spectrum = _fft(windowed)
    peak = max(range(1, size // 2), key=lambda index: abs(spectrum[index]))
    return peak * rate / size


@needs_ffmpeg
def test_speed_render_is_shorter_and_keeps_its_fundamental(tmp_path):
    """AC-4: 4 s a 2× duran 2 s y conservan la frecuencia fundamental ±2 %."""
    source = tmp_path / 'tone.wav'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-v',
            'error',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=4:sample_rate=48000',
            str(source),
        ],
        check=True,
    )
    output = tmp_path / 'speed.wav'
    doc = _doc([_track('audio')], [_clip('voice', 'audio', source.as_posix(), 0, 4, speed=2)])
    doc['version'] = 3

    render_audio.render(doc, tmp_path, output)

    assert probe_duration(output) == pytest.approx(2, abs=0.02)
    assert 'atempo=2' in output.with_suffix('.filter').read_text(encoding='utf-8')
    assert _dominant_frequency(output) == pytest.approx(_dominant_frequency(source), rel=0.02)
