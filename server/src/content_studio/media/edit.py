"""Recortar, unir y dividir (spec 015, D-5). Solo stdlib; ffmpeg por subproceso.

`remove` reusa el render del limpiador: cada tramo lleva un fundido de 15 ms y se une sin solaparse, así que la duración
es exacta. `keep` recorta y pone los fundidos pedidos. Unir con crossfade usa `xfade` y `acrossfade`; sin crossfade,
`concat`. Dividir recodifica cada parte para que el corte caiga en el instante pedido, salvo que se pida `copy`.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from content_studio.clean import render as clean_render
from content_studio.common import ffmpeg as ff

AUDIO_RATE = 48000


def has_video(path: Path | str) -> bool:
    """¿Tiene `path` un stream de video?"""
    out = subprocess.run(
        [
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'v',
            '-show_entries',
            'stream=codec_type',
            '-of',
            'csv=p=0',
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return bool(out.strip())


def fade_filters(kind: str, length: float, fade_in: float, fade_out: float) -> str:
    """Los fundidos de un tramo de `length` segundos: `kind` es `afade` (audio) o `fade` (video)."""
    parts = []
    if fade_in > 0:
        parts.append(f'{kind}=t=in:st=0:d={fade_in}')
    if fade_out > 0:
        parts.append(f'{kind}=t=out:st={length - fade_out}:d={fade_out}')
    return ','.join(parts)


def _audio_codec(out: Path) -> list[str]:
    """WAV en PCM de 24 bits; cualquier otro formato, en AAC a 192 kbps (como el render del limpiador)."""
    if out.suffix.lower() == '.wav':
        return ['-c:a', 'pcm_s24le']
    return ['-c:a', 'aac', '-b:a', '192k']


def _keep(source: Path, out: Path, start: float, end: float, fade_in: float, fade_out: float, video: bool) -> None:
    length = end - start
    args = ['-y', '-ss', str(start), '-t', str(length), '-i', str(source)]
    audio = fade_filters('afade', length, fade_in, fade_out)
    if video:
        picture = fade_filters('fade', length, fade_in, fade_out)
        args += ['-map', '0:v:0', '-map', '0:a:0', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', *_audio_codec(out)]
        if picture:
            args += ['-vf', picture]
    else:
        args += ['-map', '0:a:0', *_audio_codec(out)]
    if audio:
        args += ['-af', audio]
    ff.ffmpeg(*args, str(out))


def trim(
    source: Path | str,
    out: Path | str,
    *,
    start: float,
    end: float,
    mode: str = 'keep',
    fade_in: float = 0.0,
    fade_out: float = 0.0,
) -> None:
    """Recorta `source` en `out`: `keep` deja `start`–`end` con fundidos; `remove` quita ese tramo y une el resto."""
    if mode not in ('keep', 'remove'):
        raise ValueError(f'unknown trim mode: {mode}')
    source, out = Path(source), Path(out)
    video = has_video(source)
    if mode == 'keep':
        _keep(source, out, start, end, fade_in, fade_out, video)
        return
    length = ff.probe_duration(source)
    keep = [span for span in ((0.0, start), (end, length)) if span[1] > span[0]]
    if video:
        clean_render.render_video(source, keep, out, nvenc=False)
    else:
        clean_render.render_audio(source, keep, out)


def _audio_joins(count: int, crossfade: float) -> list[str]:
    """Une los audios [a0]…[a{count-1}] en [aout], con corte directo o con un crossfade de `crossfade` segundos."""
    if count == 1:
        return ['[a0]anull[aout]']
    if crossfade <= 0:
        return [''.join(f'[a{i}]' for i in range(count)) + f'concat=n={count}:v=0:a=1[aout]']
    chains, previous = [], 'a0'
    for i in range(1, count):
        label = 'aout' if i == count - 1 else f'x{i}'
        chains.append(f'[{previous}][a{i}]acrossfade=d={crossfade}[{label}]')
        previous = label
    return chains


def _video_joins(durations: Sequence[float], crossfade: float) -> list[str]:
    """Une los videos [v0]…[v{n-1}] en [vout] con `xfade`: cada paso empieza `crossfade` antes del anterior."""
    chains, previous, length = [], 'v0', durations[0]
    for i in range(1, len(durations)):
        label = 'vout' if i == len(durations) - 1 else f'w{i}'
        chains.append(
            f'[{previous}][v{i}]xfade=transition=fade:duration={crossfade}:offset={length - crossfade}[{label}]'
        )
        length += durations[i] - crossfade
        previous = label
    return chains


def _concat_audio(paths: Sequence[Path], out: Path, crossfade: float) -> None:
    inputs = [part for path in paths for part in ('-i', str(path))]
    normalize = [
        f'[{i}:a]aresample={AUDIO_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]'
        for i in range(len(paths))
    ]
    graph = ';'.join(normalize + _audio_joins(len(paths), crossfade))
    ff.ffmpeg('-y', *inputs, '-filter_complex', graph, '-map', '[aout]', *_audio_codec(out), str(out))


def _concat_video(paths: Sequence[Path], out: Path, crossfade: float) -> None:
    width, height = ff.video_size(paths[0])
    fps = clean_render.frames_per_second(paths[0])
    inputs = [part for path in paths for part in ('-i', str(path))]
    chains: list[str] = []
    for i in range(len(paths)):
        chains.append(
            f'[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,'
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{i}]'
        )
        chains.append(f'[{i}:a]aresample={AUDIO_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]')
    if crossfade <= 0:
        pairs = ''.join(f'[v{i}][a{i}]' for i in range(len(paths)))
        chains.append(f'{pairs}concat=n={len(paths)}:v=1:a=1[vout][aout]')
    else:
        durations = [ff.probe_duration(path) for path in paths]
        chains += _video_joins(durations, crossfade) + _audio_joins(len(paths), crossfade)
    ff.ffmpeg(
        '-y',
        *inputs,
        '-filter_complex',
        ';'.join(chains),
        '-map',
        '[vout]',
        '-map',
        '[aout]',
        '-r',
        str(fps),
        '-c:v',
        'libx264',
        '-pix_fmt',
        'yuv420p',
        '-c:a',
        'aac',
        '-b:a',
        '192k',
        str(out),
    )


def concat(sources: Sequence[Path | str], out: Path | str, *, crossfade: float = 0.0) -> None:
    """Une `sources` en `out`, con `crossfade` segundos de fundido entre clips (0, corte directo).

    Los videos se llevan a la resolución, los fps y el formato del primero. Audio con video da `mixed_kinds`.
    """
    paths = [Path(source) for source in sources]
    kinds = {has_video(path) for path in paths}
    if len(kinds) > 1:
        raise ValueError('mixed_kinds')
    if kinds == {True}:
        _concat_video(paths, Path(out), crossfade)
    else:
        _concat_audio(paths, Path(out), crossfade)


def split(
    source: Path | str,
    out_dir: Path | str,
    stem: str,
    *,
    every_seconds: float | None = None,
    markers: Sequence[float] | None = None,
    exact: bool = True,
) -> list[Path]:
    """Parte `source` cada `every_seconds` o en los `markers`, en `out_dir/<stem>-01.<ext>`, `-02`, …

    Recodifica para que el corte sea exacto; con `exact=False` copia el stream y el corte cae en un keyframe.
    """
    source, out_dir = Path(source), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = []
    for number, (start, end) in enumerate(_bounds(ff.probe_duration(source), every_seconds, markers), start=1):
        part = out_dir / f'{stem}-{number:02d}{source.suffix}'
        args = ['-y', '-ss', str(start), '-t', str(end - start), '-i', str(source), '-map', '0:v?', '-map', '0:a?']
        if not exact:
            args += ['-c', 'copy']
        ff.ffmpeg(*args, str(part))
        parts.append(part)
    return parts


def _bounds(length: float, every_seconds: float | None, markers: Sequence[float] | None) -> list[tuple[float, float]]:
    """Los tramos de `length` segundos: cada `every_seconds`, o entre los `markers`. Un marcador fuera de (0, length) no
    corta nada."""
    if markers:
        cuts = [0.0, *markers, length]
    elif every_seconds:
        cuts = [0.0, *(k * every_seconds for k in range(1, math.ceil(length / every_seconds))), length]
    else:
        raise ValueError('split needs markers or every_seconds')
    cuts = sorted({cut for cut in cuts if 0 <= cut <= length})
    return list(zip(cuts, cuts[1:], strict=False))


def build_parser() -> argparse.ArgumentParser:
    """Los subcomandos del servicio: trim, concat y split."""
    parser = argparse.ArgumentParser(prog='edit', description='Trim, join or split media files.')
    actions = parser.add_subparsers(dest='action', required=True)
    trim_p = actions.add_parser('trim', help='keep or remove a span')
    trim_p.add_argument('--input', required=True)
    trim_p.add_argument('--out', required=True)
    trim_p.add_argument('--start', type=float, required=True)
    trim_p.add_argument('--end', type=float, required=True)
    trim_p.add_argument('--mode', choices=('keep', 'remove'), default='keep')
    trim_p.add_argument('--fade-in', type=float, default=0.0)
    trim_p.add_argument('--fade-out', type=float, default=0.0)
    concat_p = actions.add_parser('concat', help='join files one after another')
    concat_p.add_argument('--input', nargs='+', required=True)
    concat_p.add_argument('--out', required=True)
    concat_p.add_argument('--crossfade', type=float, default=0.0)
    split_p = actions.add_parser('split', help='split a file every N seconds or at markers')
    split_p.add_argument('--input', required=True)
    split_p.add_argument('--out-dir', required=True)
    split_p.add_argument('--stem', required=True)
    cut = split_p.add_mutually_exclusive_group(required=True)
    cut.add_argument('--every', type=float)
    cut.add_argument('--markers', type=float, nargs='+')
    split_p.add_argument('--copy', action='store_true', help='copy the streams: cuts land on keyframes')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: corre el subcomando pedido."""
    args = build_parser().parse_args(argv)
    if args.action == 'trim':
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        trim(
            args.input,
            args.out,
            start=args.start,
            end=args.end,
            mode=args.mode,
            fade_in=args.fade_in,
            fade_out=args.fade_out,
        )
    elif args.action == 'concat':
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        concat(args.input, args.out, crossfade=args.crossfade)
    else:
        split(args.input, args.out_dir, args.stem, every_seconds=args.every, markers=args.markers, exact=not args.copy)
    return 0


if __name__ == '__main__':
    sys.exit(main())
