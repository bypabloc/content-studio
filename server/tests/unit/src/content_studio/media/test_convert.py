"""AC-1 (spec 015, T1): el armador de conversión da los argumentos de ffmpeg de cada formato y rechaza un codec que el
ffmpeg del sistema no trae. Los argumentos son golden: si un formato cambia, esta prueba lo dice."""

from __future__ import annotations

import pytest

from content_studio.media import convert

AUDIO_IN = {'path': 'in.wav', 'has_video': False}
VIDEO_IN = {'path': 'in.mp4', 'has_video': True}
ALL = frozenset({'libmp3lame', 'pcm_s24le', 'pcm_s16le', 'libopus', 'libvorbis', 'aac', 'libx264', 'libx265', 'flac'})


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


def test_the_catalog_lists_every_audio_target_with_its_extension():
    """AC-1: el catálogo tiene los seis formatos de audio, cada uno con su extensión."""
    from content_studio.media.formats import TARGETS

    audio = {name for name, spec in TARGETS.items() if spec['kind'] == 'audio'}

    assert audio == {'mp3', 'wav', 'flac', 'ogg-opus', 'ogg-vorbis', 'm4a'}
    assert TARGETS['ogg-opus']['ext'] == '.ogg'
