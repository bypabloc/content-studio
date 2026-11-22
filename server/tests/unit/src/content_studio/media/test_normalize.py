"""AC-6 (spec 015, D-4, T5): normalizar a LUFS en dos pasadas. Un audio de -30 LUFS pasa a -16 ± 0,5 con pico real de
-1 dBTP o menos; en un video el stream de video sale copiado; una ruta dentro de `reference/` se rechaza. Los medios son
fixtures generadas aquí con ffmpeg; sin ffmpeg, las pruebas que lo usan se saltan."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio import paths
from content_studio.media import normalize

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')


def test_the_presets_are_youtube_minus_14_podcast_minus_16_and_broadcast_minus_23():
    """D-4: cada preset fija el objetivo integrado; `custom` toma el suyo."""
    assert normalize.target_lufs('youtube') == -14.0
    assert normalize.target_lufs('podcast') == -16.0
    assert normalize.target_lufs('broadcast') == -23.0
    assert normalize.target_lufs('custom', custom=-18.0) == -18.0


def test_the_second_pass_is_linear_and_carries_the_first_pass_measurements():
    """AC-6: la segunda pasada usa los `measured_*` de la primera, `linear=true` y el pico de -1 dBTP."""
    first = {
        'input_i': '-30.0',
        'input_tp': '-10.0',
        'input_lra': '0.0',
        'input_thresh': '-40.0',
        'target_offset': '0.5',
    }

    chain = normalize.second_pass(first, target=-16.0)

    assert 'linear=true' in chain
    assert 'measured_I=-30.0' in chain and 'measured_TP=-10.0' in chain and 'measured_LRA=0.0' in chain
    assert 'measured_thresh=-40.0' in chain and 'offset=0.5' in chain
    assert 'I=-16.0' in chain and 'TP=-1.0' in chain


def test_the_enhance_chain_runs_before_the_loudness_filter_in_the_first_pass():
    """«Mejorar voz» va antes de loudnorm, con la cadena fija de D-4; así la medición ya la incluye."""
    chain = normalize.first_pass(target=-16.0, enhance=True)

    assert chain.startswith(normalize.ENHANCE + ',loudnorm=')
    assert (
        normalize.ENHANCE == 'highpass=f=80,deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150'
    )
    assert normalize.first_pass(target=-16.0, enhance=False).startswith('loudnorm=')


def test_a_source_inside_reference_is_refused_with_its_code():
    """AC-6: una ruta dentro de `reference/` falla con `reference_protected`; cualquier otra ruta pasa."""
    assert normalize.reference_error(paths.references_dir() / 'voz' / 'a.wav') == {
        'code': 'reference_protected',
        'params': {},
    }
    assert normalize.reference_error(Path('out') / 'a.wav') is None


def test_the_output_codec_is_fixed_by_the_container_with_a_bitrate():
    """Con AAC, Opus o MP3 el bitrate va fijo (el valor por defecto del codificador movió el nivel); WAV y FLAC no."""
    assert normalize.audio_args('a.mp4') == ['-c:a', 'aac', '-b:a', '192k']
    assert normalize.audio_args('a.webm') == ['-c:a', 'libopus', '-b:a', '160k']
    assert normalize.audio_args('a.wav') == []


def _pink(path: Path, seconds: float = 10) -> Path:
    """Ruido rosa a -30 LUFS (a 0 dB mide -20,6 LUFS, así que se baja 9,4 dB). Más parecido a voz que un tono: con un
    tono puro loudnorm cae a dinámico, y el AC no lo pide."""
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
            f'anoisesrc=color=pink:duration={seconds}:amplitude=0.5:seed=7',
            '-af',
            'volume=-9.4dB',
            '-c:a',
            'pcm_s24le',
            str(path),
        ],
        check=True,
    )
    return path


def _video_md5(path: Path) -> str:
    """El hash de los paquetes del stream de video, sin decodificar: copiarlo tal cual da el mismo."""
    return subprocess.run(
        [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-i',
            str(path),
            '-map',
            '0:v',
            '-c',
            'copy',
            '-f',
            'md5',
            '-',
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@needs_ffmpeg
def test_ac6_thirty_lufs_becomes_sixteen_with_a_true_peak_under_minus_one(tmp_path):
    """AC-6: un audio de -30 LUFS normalizado a `podcast` mide -16 ± 0,5 LUFS con pico real de -1 dBTP o menos."""
    source = _pink(tmp_path / 'source.wav')
    out = tmp_path / 'normalized.wav'

    report = normalize.normalize(source, out, target=-16.0)

    assert -30.5 <= report['before']['I'] <= -29.5  # el fixture está donde dice el AC
    after = normalize.measure(out)
    assert abs(after['I'] + 16.0) <= 0.5
    assert after['TP'] <= -1.0
    assert report['mode'] == 'linear'


@needs_ffmpeg
def test_ac6_a_video_keeps_its_video_packets_and_only_the_audio_changes(tmp_path):
    """AC-6: en un video el stream de video sale copiado (mismo hash de paquetes) y el audio queda a -16 LUFS."""
    source = tmp_path / 'clip.mp4'
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
            'testsrc2=size=320x240:rate=25:duration=10',
            '-f',
            'lavfi',
            '-i',
            'anoisesrc=color=pink:duration=10:amplitude=0.5:seed=7',
            '-filter_complex',
            '[1:a]volume=-9.4dB[a]',
            '-map',
            '0:v',
            '-map',
            '[a]',
            '-c:v',
            'libx264',
            '-c:a',
            'aac',
            str(source),
        ],
        check=True,
    )
    out = tmp_path / 'normalized.mp4'

    normalize.normalize(source, out, target=-16.0)

    assert _video_md5(source) == _video_md5(out)
    assert abs(normalize.measure(out)['I'] + 16.0) <= 0.5


def test_a_custom_preset_needs_its_target():
    with pytest.raises(ValueError, match='custom preset needs a target'):
        normalize.target_lufs('custom')


def test_each_container_gets_its_own_output_codec():
    assert normalize.audio_args('a.mp3') == ['-c:a', 'libmp3lame', '-b:a', '192k']
    assert normalize.audio_args('a.MOV') == ['-c:a', 'aac', '-b:a', '192k']


def test_a_report_without_a_loudness_range_is_an_error(monkeypatch):
    """Si ffmpeg no imprime el rango de sonoridad, la medición falla en vez de dar un LRA inventado."""
    monkeypatch.setattr(normalize.ff, 'ffmpeg', lambda *args: 'Integrated loudness: -16.0\n')
    monkeypatch.setattr(normalize.ff, 'parse_loudness', lambda report: (-16.0, -1.0))

    with pytest.raises(ValueError, match='no loudness range'):
        normalize.measure('a.wav')


def test_the_cli_writes_the_report_as_json(monkeypatch, tmp_path):
    """La CLI llama a `normalize` con el preset traducido a LUFS y escribe el reporte en JSON."""
    report = {
        'before': {'I': -30.0, 'TP': -10.0, 'LRA': 4.0},
        'after': {'I': -16.0, 'TP': -1.2, 'LRA': 3.5},
        'mode': 'linear',
        'target': -16.0,
    }
    seen: dict = {}

    def fake(source, out, *, target, enhance):
        seen.update(source=source, out=out, target=target, enhance=enhance)
        return report

    monkeypatch.setattr(normalize, 'normalize', fake)
    report_path = tmp_path / 'report.json'

    code = normalize.main(
        ['--input', 'a.wav', '--out', 'b.wav', '--preset', 'podcast', '--report', str(report_path), '--enhance']
    )

    assert code == 0
    assert json.loads(report_path.read_text(encoding='utf-8')) == report
    assert seen == {'source': 'a.wav', 'out': 'b.wav', 'target': -16.0, 'enhance': True}


def test_the_custom_preset_without_a_target_is_a_usage_error(tmp_path):
    with pytest.raises(SystemExit):
        normalize.main(
            ['--input', 'a.wav', '--out', 'b.wav', '--preset', 'custom', '--report', str(tmp_path / 'r.json')]
        )
