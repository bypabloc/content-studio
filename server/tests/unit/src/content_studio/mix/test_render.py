import hashlib
import shutil
import subprocess
import wave
from array import array
from math import log10
from pathlib import Path

import pytest

from content_studio.common.ffmpeg import probe_duration
from content_studio.mix import render

needs_ffmpeg = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='necesita ffmpeg en el PATH')
VOICE_REGIONS = [(0.0, 1.0), (2.0, 3.0), (4.0, 5.0)]  # los tramos con tono de la voz sintética, en su propio tiempo


def _make(out: Path, *args: str) -> Path:
    """Corre ffmpeg con `args` y escribe `out`."""
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *args, str(out)], check=True)
    return out


def _voice(folder: Path) -> Path:
    """Seis segundos de voz sintética: un tono de 1 kHz en 0–1, 2–3 y 4–5 s, y silencio entre ellos."""
    expr = '0.5*sin(2*PI*1000*t)*(between(t,0,1)+between(t,2,3)+between(t,4,5))'
    return _make(folder / 'voice.wav', '-f', 'lavfi', '-i', f"aevalsrc=exprs='{expr}':s=48000:d=6")


def _music(folder: Path, seconds: float) -> Path:
    """Ruido rosa de `seconds` s: la música sintética."""
    return _make(folder / 'music.wav', '-f', 'lavfi', '-i', f'anoisesrc=d={seconds}:color=pink:r=48000:a=0.2')


def _read(path: Path) -> tuple[int, list[float]]:
    """La tasa y las muestras en mono (de -1 a 1) de un WAV de 16 bits."""
    with wave.open(str(path)) as wav:
        rate, channels = wav.getframerate(), wav.getnchannels()
        samples = array('h', wav.readframes(wav.getnframes()))
    return rate, [sample / 32768 for sample in samples[::channels]]


def _rms_db(samples: list[float], rate: int, start: float, end: float) -> float:
    """El nivel RMS en dB de la ventana [start, end) en segundos."""
    window = samples[int(start * rate) : int(end * rate)]
    return 10 * log10(sum(sample * sample for sample in window) / len(window))


def _without_tone(source: Path, folder: Path) -> Path:
    """La mezcla sin el tono de 1 kHz: una muesca estrecha deja casi solo la música."""
    return _make(folder / 'notch.wav', '-i', str(source), '-af', 'bandreject=f=1000:width_type=h:w=100')


@needs_ffmpeg
def test_ac3_transcript_ducking_lowers_the_music_about_12_db_inside_the_voice(tmp_path):
    """AC-3: con ducking por transcripción de -12 dB, la música baja unos 12 dB dentro de los tramos de voz, y el LUFS
    final es -14 con TP ≤ -1. La voz empieza a 1 s (intro), así que los tramos quedan en 1–2 y 3–4 s de la salida."""
    voice, music = _voice(tmp_path), _music(tmp_path, seconds=10)
    out = tmp_path / 'mix.wav'

    report = render.render(
        voice, music, out, regions=VOICE_REGIONS, mode='transcript', duck_db=-12.0, ramp=0.3, intro=1.0
    )

    rate, samples = _read(_without_tone(out, tmp_path))
    inside = [_rms_db(samples, rate, 1.2, 1.8), _rms_db(samples, rate, 3.2, 3.8)]
    outside = [_rms_db(samples, rate, 2.4, 2.6), _rms_db(samples, rate, 4.4, 4.6)]
    drop = sum(outside) / len(outside) - sum(inside) / len(inside)
    assert drop == pytest.approx(12, abs=1.5)
    assert report['after']['I'] == pytest.approx(-14, abs=0.5)
    assert report['after']['TP'] <= -1


@needs_ffmpeg
def test_ac4_music_shorter_than_the_mix_fails_with_music_too_short(tmp_path):
    """AC-4: si la música dura menos que intro + voz + outro (8 s), el trabajo falla con `music_too_short`."""
    with pytest.raises(render.MixError) as caught:
        render.render(
            _voice(tmp_path),
            _music(tmp_path, seconds=4),
            tmp_path / 'mix.wav',
            regions=VOICE_REGIONS,
            intro=1.0,
            outro=1.0,
        )

    assert caught.value.code == 'music_too_short'


@needs_ffmpeg
def test_ac4_longer_music_is_cut_to_the_mix_length_and_the_inputs_stay_untouched(tmp_path):
    """AC-4: la salida dura intro + voz + outro (8 s) ± 10 ms, y las pistas de entrada no cambian."""
    voice, music = _voice(tmp_path), _music(tmp_path, seconds=12)
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (voice, music)}
    out = tmp_path / 'mix.wav'

    render.render(voice, music, out, regions=VOICE_REGIONS, intro=1.0, outro=1.0)

    assert probe_duration(out) == pytest.approx(8, abs=0.01)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (voice, music)} == before


@needs_ffmpeg
def test_sidechain_mode_renders_the_mix_length_at_the_target_loudness(tmp_path):
    """El modo sidechain (la voz controla la música con sidechaincompress) da la misma duración y el mismo LUFS."""
    out = tmp_path / 'mix.wav'

    report = render.render(
        _voice(tmp_path),
        _music(tmp_path, seconds=12),
        out,
        regions=VOICE_REGIONS,
        mode='sidechain',
        intro=1.0,
        outro=1.0,
    )

    assert probe_duration(out) == pytest.approx(8, abs=0.01)
    assert report['after']['I'] == pytest.approx(-14, abs=0.5)


VIDEO_TONES = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]  # los tonos del audio del video, en su tiempo


def _video(folder: Path) -> Path:
    """Ocho segundos de video (una tira de colores) con su audio: un tono de 1 kHz en 1–2, 3–4 y 5–6 s."""
    tone = '0.5*sin(2*PI*1000*t)*(between(t,1,2)+between(t,3,4)+between(t,5,6))'
    return _make(
        folder / 'video.mp4',
        '-f',
        'lavfi',
        '-i',
        'testsrc=size=320x240:rate=25:duration=8',
        '-f',
        'lavfi',
        '-i',
        f"aevalsrc=exprs='{tone}':s=48000:d=8",
        '-c:v',
        'libx264',
        '-pix_fmt',
        'yuv420p',
        '-c:a',
        'aac',
    )


def _video_md5(path: Path) -> str:
    """El hash del stream de video tal cual está, sin recodificar: H.264 en bruto."""
    data = subprocess.run(
        ['ffmpeg', '-loglevel', 'error', '-i', str(path), '-map', '0:v:0', '-c:v', 'copy', '-f', 'h264', '-'],
        capture_output=True,
        check=True,
    ).stdout
    return hashlib.md5(data).hexdigest()


def _tone_samples(path: Path, folder: Path) -> tuple[int, list[float]]:
    """El audio del video con solo la banda de 1 kHz (la voz de tono), en mono y de -1 a 1."""
    tone = _make(folder / 'tone.wav', '-i', str(path), '-vn', '-af', 'bandpass=f=1000:width_type=h:w=100', '-ac', '1')
    with wave.open(str(tone)) as wav:
        rate = wav.getframerate()
        samples = array('h', wav.readframes(wav.getnframes()))
    return rate, [sample / 32768 for sample in samples]


@needs_ffmpeg
@pytest.mark.parametrize('video_mode', ['replace', 'under'])
def test_ac5_the_video_stream_is_copied_and_the_audio_lasts_as_long_as_it(tmp_path, video_mode):
    """AC-5: con `replace` y con `under`, el stream de video sale igual que el original y el audio dura lo mismo que
    el video (± 1 cuadro). En `under`, la voz original sigue presente: su tono se oye por encima de las pausas."""
    video = _video(tmp_path)
    out = tmp_path / 'mix.mp4'
    if video_mode == 'replace':
        voice, intro, outro, regions = _voice(tmp_path), 1.0, 1.0, VOICE_REGIONS
    else:
        voice, intro, outro, regions = None, 0.0, 0.0, VIDEO_TONES

    render.render(
        voice,
        _music(tmp_path, seconds=12),
        out,
        regions=regions,
        intro=intro,
        outro=outro,
        video=video,
        video_mode=video_mode,
    )

    assert _video_md5(out) == _video_md5(video)
    assert probe_duration(out) == pytest.approx(probe_duration(video), abs=1 / 25)
    rate, samples = _tone_samples(out, tmp_path)
    tone = _rms_db(samples, rate, 1.2, 1.8)
    pause = _rms_db(samples, rate, 2.4, 2.6)
    assert tone - pause >= 20
