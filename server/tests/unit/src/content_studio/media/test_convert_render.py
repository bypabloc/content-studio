"""AC-2 y AC-3 (spec 015, T2): la conversión real con ffmpeg da el códec, los canales, la frecuencia y la resolución
pedidos, la duración igual, y el GIF tiene los cuadros y el ancho pedidos. Los medios son fixtures generadas aquí; los
formatos que el ffmpeg del equipo no trae se saltan."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.media import convert

pytestmark = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def _encoders() -> frozenset[str]:
    """Los nombres de los codificadores que trae el ffmpeg de este equipo (`ffmpeg -encoders`)."""
    out = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True, check=True).stdout
    rows = (line.split() for line in out.splitlines())
    # Cada fila: banderas (V/A/S + letras), nombre, descripción. Las cabeceras no tienen banderas de ese formato.
    return frozenset(
        row[1] for row in rows if len(row) >= 2 and row[0][:1] in {'V', 'A', 'S'} and set(row[0]) <= set('VASFXBDIL.')
    )


ENCODERS = _encoders()


def _probe(path: Path) -> dict:
    """Los streams y el formato de un archivo, con ffprobe en JSON."""
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)


def _stream(info: dict, kind: str) -> dict:
    """El primer stream del tipo pedido (`audio` o `video`)."""
    return next(s for s in info['streams'] if s['codec_type'] == kind)


def _wav(tmp_path: Path) -> Path:
    """Dos segundos de tono en estéreo a 44,1 kHz."""
    path = tmp_path / 'in.wav'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=2',
            '-ac',
            '2',
            '-ar',
            '44100',
            str(path),
        ],
        check=True,
    )
    return path


def _mp4(tmp_path: Path, seconds: float = 2) -> Path:
    """Un video de 640×480 a 25 fps con tono en el audio."""
    path = tmp_path / 'in.mp4'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            f'testsrc2=size=640x480:rate=25:duration={seconds}',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=330:duration={seconds}',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-shortest',
            str(path),
        ],
        check=True,
    )
    return path


def _decoded_seconds(path: Path) -> float:
    """La duración que se reproduce: el tiempo final que ffmpeg mide al decodificar. El relleno del codificador (LAME,
    por ejemplo) cuenta en la duración del contenedor, pero no al decodificar."""
    err = subprocess.run(
        ['ffmpeg', '-hide_banner', '-i', str(path), '-f', 'null', '-'], capture_output=True, text=True, check=True
    ).stderr
    hours, minutes, seconds = re.findall(r'time=(\d+):(\d+):(\d+\.\d+)', err)[-1]
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


AUDIO_CASES = [
    # destino, códec que debe reportar ffprobe, codificador que hace falta, frecuencia pedida
    ('mp3', 'mp3', 'libmp3lame', 22050),
    ('wav', 'pcm_s16le', 'pcm_s16le', 22050),
    ('flac', 'flac', 'flac', 22050),
    ('ogg-opus', 'opus', 'libopus', 48000),  # Opus solo codifica 8, 12, 16, 24 y 48 kHz
    ('ogg-vorbis', 'vorbis', 'libvorbis', 22050),
    ('m4a', 'aac', 'aac', 22050),
]


@pytest.mark.parametrize(('target', 'codec', 'encoder', 'rate'), AUDIO_CASES)
def test_ac2_each_audio_format_has_the_requested_codec_channels_rate_and_duration(
    tmp_path, target, codec, encoder, rate
):
    """AC-2: un WAV de 2 s a cada formato de audio, mono y a la frecuencia que el formato admite: el códec, los canales,
    la frecuencia y la duración que se reproduce (± 50 ms) son los pedidos."""
    if encoder not in ENCODERS:
        pytest.skip(f'el ffmpeg de este equipo no trae {encoder}')
    out = tmp_path / f'out{convert.TARGETS[target]["ext"]}'
    options = {'channels': 1, 'sample_rate': rate}

    convert.run({'path': str(_wav(tmp_path)), 'has_video': False}, target, options, out, encoders=ENCODERS)

    audio = _stream(_probe(out), 'audio')
    assert audio['codec_name'] == codec
    assert audio['channels'] == 1
    assert int(audio['sample_rate']) in {rate, 48000}  # Opus reporta su tasa interna de 48 kHz en el contenedor
    assert abs(_decoded_seconds(out) - 2.0) < 0.05


VIDEO_CASES = [
    # destino, códec de video que debe reportar ffprobe, codificador que hace falta
    ('mp4-h264', 'h264', 'libx264'),
    ('mp4-h265', 'hevc', 'libx265'),
    ('webm-vp9', 'vp9', 'libvpx-vp9'),
    ('webm-av1', 'av1', 'libsvtav1'),
    ('mov', 'h264', 'libx264'),
    ('mkv', 'h264', 'libx264'),
]


@pytest.mark.parametrize(('target', 'codec', 'encoder'), VIDEO_CASES)
def test_ac2_each_video_format_has_the_requested_codec_resolution_and_duration(tmp_path, target, codec, encoder):
    """AC-2: un MP4 de 640×480 de 2 s a cada formato de video, a 240 px de alto: el códec, la resolución (manteniendo
    el aspecto) y la duración (± 1 cuadro a 25 fps) son los pedidos."""
    if encoder not in ENCODERS:
        pytest.skip(f'el ffmpeg de este equipo no trae {encoder}')
    out = tmp_path / f'out{convert.TARGETS[target]["ext"]}'

    convert.run({'path': str(_mp4(tmp_path)), 'has_video': True}, target, {'resolution': 240}, out, encoders=ENCODERS)

    video = _stream(_probe(out), 'video')
    assert video['codec_name'] == codec
    assert (video['width'], video['height']) == (320, 240)
    assert abs(_decoded_seconds(out) - 2.0) <= 0.04 + 0.01  # ± 1 cuadro a 25 fps, más la tolerancia del contenedor


def test_ac3_a_gif_has_150_frames_and_480_px_from_a_10_second_clip(tmp_path):
    """AC-3: un video de 10 s a 25 fps → GIF de 15 fps y 480 px de ancho: 150 ± 2 cuadros y 480 px."""
    out = tmp_path / 'out.gif'

    convert.run(
        {'path': str(_mp4(tmp_path, seconds=10)), 'has_video': True},
        'gif',
        {'fps': 15, 'width': 480},
        out,
        encoders=ENCODERS,
    )

    video = _stream(_probe(out), 'video')
    frames = int(
        json.loads(
            subprocess.run(
                [
                    'ffprobe',
                    '-v',
                    'error',
                    '-count_frames',
                    '-select_streams',
                    'v:0',
                    '-show_entries',
                    'stream=nb_read_frames',
                    '-of',
                    'json',
                    str(out),
                ],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )['streams'][0]['nb_read_frames']
    )
    assert video['width'] == 480
    assert abs(frames - 150) <= 2
