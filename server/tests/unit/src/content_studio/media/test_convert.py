"""AC-1 (spec 015, T1): el armador de conversión da los argumentos de ffmpeg de cada formato y rechaza un codec que el
ffmpeg del sistema no trae. Los argumentos son golden: si un formato cambia, esta prueba lo dice.
AC-2 y AC-3 (T2) convierten de verdad con ffmpeg: los medios son fixtures generadas aquí y se saltan sin ffmpeg."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.media import convert

AUDIO_IN = {'path': 'in.wav', 'has_video': False}
VIDEO_IN = {'path': 'in.mp4', 'has_video': True}
ALL = frozenset({'libmp3lame', 'pcm_s24le', 'pcm_s16le', 'libopus', 'libvorbis', 'aac', 'libx264', 'libx265', 'flac'})
needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def test_mp3_vbr_v2_is_the_default_quality_of_the_audio_formats():
    """Un MP3 VBR V2 de un WAV: codec, calidad VBR y sin video."""
    args = convert.build(AUDIO_IN, 'mp3', {'vbr': 2}, ALL)

    assert args == ['-y', '-i', 'in.wav', '-c:a', 'libmp3lame', '-q:a', '2']


def test_wav_depth_picks_the_pcm_codec():
    """WAV de 24 bits: el códec pcm_s24le."""
    assert convert.build(AUDIO_IN, 'wav', {'depth': 24}, ALL) == ['-y', '-i', 'in.wav', '-c:a', 'pcm_s24le']


def test_flac_level_and_ogg_quality_are_golden():
    """FLAC con nivel de compresión 8 y Ogg Vorbis con calidad 5: argumentos exactos."""
    assert convert.build(AUDIO_IN, 'flac', {'level': 8}, ALL) == [
        '-y',
        '-i',
        'in.wav',
        '-c:a',
        'flac',
        '-compression_level',
        '8',
    ]
    assert convert.build(AUDIO_IN, 'ogg-vorbis', {'quality': 5}, ALL) == [
        '-y',
        '-i',
        'in.wav',
        '-c:a',
        'libvorbis',
        '-q:a',
        '5',
    ]


def test_opus_bitrate_channels_and_rate_go_after_the_codec():
    """Ogg Opus a 96 kbps, mono y a 48 kHz: los filtros de canales y frecuencia van después del códec."""
    args = convert.build(AUDIO_IN, 'ogg-opus', {'bitrate': 96, 'channels': 1, 'sample_rate': 48000}, ALL)

    assert args == ['-y', '-i', 'in.wav', '-c:a', 'libopus', '-b:a', '96k', '-ac', '1', '-ar', '48000']


def test_opus_refuses_a_rate_it_cannot_encode():
    """Opus solo codifica 8, 12, 16, 24 y 48 kHz: otra frecuencia da `sample_rate_unsupported`, sin llegar a ffmpeg."""
    with pytest.raises(convert.ConvertError) as caught:
        convert.build(AUDIO_IN, 'ogg-opus', {'sample_rate': 22050}, ALL)

    assert caught.value.code == 'sample_rate_unsupported'
    assert caught.value.params == {'codec': 'libopus', 'rate': 22050}


def test_video_to_audio_drops_the_video_stream():
    """Extraer audio de un video: `-vn`, para que el contenedor no lleve el video."""
    args = convert.build(VIDEO_IN, 'm4a', {'bitrate': 192}, ALL)

    assert args == ['-y', '-i', 'in.mp4', '-vn', '-c:a', 'aac', '-b:a', '192k']


def test_mp4_h264_uses_the_shared_encoder_and_aac_audio():
    """Un MP4 H.264 con el codificador compartido (libx264 sin NVENC) y AAC."""
    args = convert.build(VIDEO_IN, 'mp4-h264', {}, ALL)

    assert args == [
        '-y',
        '-i',
        'in.mp4',
        '-c:v',
        'libx264',
        '-crf',
        '18',
        '-preset',
        'medium',
        '-c:a',
        'aac',
        '-b:a',
        '192k',
    ]


def test_a_social_preset_with_reframe_keeps_its_frame_rate():
    """Un preset de red (1080x1920 a 30 fps) con encuadre: la salida sale a 30 fps, no a los de la fuente."""
    options = {'width': 1080, 'height': 1920, 'fps': 30, 'reframe': {'mode': 'center'}}

    args = convert.build(VIDEO_IN, 'mp4-h264', options, ALL)

    assert args[args.index('-r') + 1] == '30'


def test_a_codec_missing_from_the_system_ffmpeg_is_refused_with_its_name():
    """Un codec que el ffmpeg del sistema no trae da `codec_unavailable`, con el nombre del codec."""
    with pytest.raises(convert.ConvertError) as caught:
        convert.build(AUDIO_IN, 'ogg-opus', {}, frozenset({'libvorbis'}))

    assert caught.value.code == 'codec_unavailable'
    assert caught.value.params == {'codec': 'libopus'}


def test_an_unknown_target_is_refused():
    """Un formato que no está en el catálogo da `unknown_target`."""
    with pytest.raises(convert.ConvertError) as caught:
        convert.build(AUDIO_IN, 'aiff', {}, ALL)

    assert caught.value.code == 'unknown_target'


def test_the_encoders_are_the_names_ffmpeg_lists_after_its_flags():
    """`ffmpeg -encoders` lista cada códec con sus banderas de seis letras y luego su nombre."""
    listing = (
        'Encoders:\n'
        ' V..... = Video\n'
        ' V....D libx264              libx264 H.264 / AVC (codec h264)\n'
        ' A....D aac                  AAC (Advanced Audio Coding)\n'
    )

    assert convert.parse_encoders(listing) == frozenset({'libx264', 'aac'})


@needs_ffmpeg
def test_main_converts_a_wav_to_mp3_in_the_job_folder(tmp_path):
    """El CLI del conversor escribe `converted.mp3` en la carpeta del trabajo, con el códec mp3."""
    source = tmp_path / 'tone.wav'
    subprocess.run(
        ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', str(source)], check=True
    )
    job = tmp_path / 'job'

    assert convert.main(['--input', str(source), '--target', 'mp3', '--out-dir', str(job), '--options', '{}']) == 0

    out = job / 'converted.mp3'
    assert out.is_file()
    codec = subprocess.run(
        [
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'a:0',
            '-show_entries',
            'stream=codec_name',
            '-of',
            'csv=p=0',
            str(out),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert codec == 'mp3'


def test_the_catalog_lists_every_audio_target_with_its_extension():
    """AC-1: el catálogo tiene los seis formatos de audio, cada uno con su extensión."""
    from content_studio.media.formats import TARGETS

    audio = {name for name, spec in TARGETS.items() if spec['kind'] == 'audio'}

    assert audio == {'mp3', 'wav', 'flac', 'ogg-opus', 'ogg-vorbis', 'm4a'}
    assert TARGETS['ogg-opus']['ext'] == '.ogg'


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
@needs_ffmpeg
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
@needs_ffmpeg
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


@needs_ffmpeg
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
