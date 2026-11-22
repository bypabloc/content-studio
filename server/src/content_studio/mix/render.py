"""Render de la mezcla (spec 016, D-2): ducking, intro y outro, y LUFS final. Corre ffmpeg por subproceso.

La voz se desplaza `intro` s y la música se corta a intro + voz + outro con un fade. El ducking baja la música con
`sendcmd` sobre su volumen (`transcript`) o con `sidechaincompress` (`sidechain`). La salida se normaliza con
`media/normalize` en dos pasadas; las pistas de entrada no cambian.
"""

from __future__ import annotations

from pathlib import Path

from content_studio.common import ffmpeg as ff
from content_studio.common import sendcmd
from content_studio.media import normalize
from content_studio.mix import envelope

# cspell:ignore sidechaincompress adelay amix asplit asendcmd: filtros de ffmpeg, que el diccionario no trae.

MODES = ('transcript', 'sidechain')
STEP_S = 0.02  # un paso de volumen cada 20 ms: dentro de las rampas, porque en los tramos planos no cambia
FADE_IN_S = 1.0  # la música entra con un fade de 1 s
FADE_OUT_S = 2.0  # y sale con 2 s, o un tercio de la mezcla si es más corta (como `music/duration.fit`)
TOLERANCE_S = 0.05  # una música más corta que esto del total ya es corta
SIDECHAIN = 'sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300:makeup=1'
DUCK = 'duck'  # el nombre del filtro de volumen de la música: `sendcmd` le manda los pasos


class MixError(Exception):
    """Un error de la mezcla con su código del catálogo (`music_too_short`, por ejemplo)."""

    def __init__(self, code: str, params: dict | None = None) -> None:
        """Guarda el código del catálogo y sus parámetros."""
        super().__init__(code)
        self.code = code
        self.params = params or {}


def render(
    voice: Path | str,
    music: Path | str,
    out: Path | str,
    *,
    regions: list[tuple[float, float]],
    mode: str = 'transcript',
    duck_db: float = -12.0,
    ramp: float = 0.3,
    music_db: float = -6.0,
    voice_db: float = 0.0,
    intro: float = 0.0,
    outro: float = 0.0,
    lufs: float = -14.0,
) -> dict:
    """Mezcla `voice` sobre `music` con ducking y escribe `out` normalizado a `lufs`. Devuelve lo medido.

    `regions` son los tramos de voz en el tiempo de la voz (sin la intro). Sin ellos, `transcript` no baja nada.
    """
    if mode not in MODES:
        raise MixError('unknown_mix_mode', {'mode': mode})
    voice, music, out = Path(voice), Path(music), Path(out)
    total = intro + ff.probe_duration(voice) + outro
    music_len = ff.probe_duration(music)
    if music_len < total - TOLERANCE_S:
        raise MixError('music_too_short', {'music': round(music_len, 3), 'total': round(total, 3)})

    fade = min(FADE_OUT_S, total / 3)
    curve = envelope.gain_curve([(start + intro, end + intro) for start, end in regions], total, duck_db, ramp)
    commands = out.with_name('duck.cmd')
    commands.write_text(sendcmd.script(_duck_lines(curve, total, music_db)), encoding='utf-8')
    raw = out.with_name('mix-raw.wav')
    ff.ffmpeg(
        '-y',
        '-i',
        str(voice),
        '-i',
        str(music),
        '-filter_complex',
        _graph(mode, intro, total, fade, music_db, voice_db, commands),
        '-map',
        '[mix]',
        '-c:a',
        'pcm_s16le',
        str(raw),
    )
    report = normalize.normalize(raw, out, target=lufs)
    raw.unlink()
    return {
        'mode': mode,
        'regions': len(regions),
        'duration': round(ff.probe_duration(out), 3),
        'before': report['before'],
        'after': report['after'],
        'target': lufs,
    }


def _graph(mode: str, intro: float, total: float, fade: float, music_db: float, voice_db: float, commands: Path) -> str:
    """El filtro complejo: la voz con su intro y su volumen, la música cortada con fades, el ducking y la suma."""
    voice = f'[0:a]adelay={round(intro * 1000)}:all=1,volume={_linear(voice_db):.6f}'
    music = (
        f'[1:a]atrim=duration={total:.3f},afade=t=in:st=0:d={FADE_IN_S},'
        f'afade=t=out:st={total - fade:.3f}:d={fade:.3f}:curve=hsin'
    )
    mix = 'amix=inputs=2:normalize=0:dropout_transition=0:duration=longest[mix]'
    if mode == 'sidechain':
        return (
            f'{voice},asplit=2[side][voice];[side]apad=whole_dur={total:.3f}[key];'
            f'{music},volume={_linear(music_db):.6f}[raw];'
            f'[raw][key]{SIDECHAIN}[music];[voice][music]{mix}'
        )
    return (
        f"{voice}[voice];{music},asendcmd=f='{sendcmd.filter_path(commands)}',"
        f'volume@{DUCK}=volume={_linear(music_db):.6f}:precision=float[music];[voice][music]{mix}'
    )


def _duck_lines(curve: list[tuple[float, float]], total: float, music_db: float) -> list[tuple[float, str]]:
    """Los pasos de volumen de la música: uno cada `STEP_S` s, pero solo donde el volumen cambia (las rampas)."""
    lines: list[tuple[float, str]] = []
    last: float | None = None
    for index in range(round(total / STEP_S) + 1):
        t = min(total, index * STEP_S)
        volume = _linear(music_db + envelope.value_at(curve, t, 0.0))
        if last is None or abs(volume - last) > 1e-6:
            lines.append((round(t, 3), f'volume@{DUCK} volume {volume:.6f}'))
            last = volume
    return lines


def _linear(db: float) -> float:
    """El factor lineal de un valor en dB."""
    return 10 ** (db / 20)
