"""Normalizar a LUFS en dos pasadas (spec 015, D-4): medir con `loudnorm`, aplicar en lineal con esas medidas y medir
antes y después con `ebur128`. Solo stdlib; ffmpeg por subproceso.

En un video normaliza solo el audio y el stream de video se copia (`-c:v copy`). Las rutas dentro de `reference/` no se
procesan: son referencias de clonación.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from content_studio import paths
from content_studio.common import ffmpeg as ff

TARGETS = {'youtube': -14.0, 'podcast': -16.0, 'broadcast': -23.0}  # objetivo integrado en LUFS
PRESETS = (*TARGETS, 'custom')
ENHANCE = 'highpass=f=80,deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150'
TRUE_PEAK = -1.0  # dBTP
RANGE = 11.0  # LRA que pide loudnorm


def target_lufs(preset: str, custom: float | None = None) -> float:
    """El objetivo integrado (LUFS) del preset; `custom` toma el valor que dé el usuario."""
    if preset == 'custom':
        if custom is None:
            raise ValueError('the custom preset needs a target in LUFS')
        return custom
    return TARGETS[preset]


def _chain(enhance: bool, loudnorm: str) -> str:
    """La cadena de filtros: «mejorar voz» antes de loudnorm si `enhance`."""
    return f'{ENHANCE},{loudnorm}' if enhance else loudnorm


def first_pass(target: float, enhance: bool = False) -> str:
    """La cadena de la primera pasada: solo mide, y loudnorm escribe sus medidas en JSON."""
    return _chain(enhance, f'loudnorm=I={target}:TP={TRUE_PEAK}:LRA={RANGE}:print_format=json')


def second_pass(first: dict, target: float, enhance: bool = False) -> str:
    """La cadena de la segunda pasada: lineal, con las medidas de la primera (`measured_*`) y el mismo objetivo."""
    measured = (
        f'measured_I={first["input_i"]}:measured_TP={first["input_tp"]}:measured_LRA={first["input_lra"]}:'
        f'measured_thresh={first["input_thresh"]}:offset={first["target_offset"]}'
    )
    return _chain(
        enhance, f'loudnorm=I={target}:TP={TRUE_PEAK}:LRA={RANGE}:{measured}:linear=true:print_format=summary'
    )


def audio_args(out: Path | str) -> list[str]:
    """El códec y el bitrate del audio de salida. Con bitrate fijo, el AAC del equipo deja el mismo nivel que se midió;
    con el valor por defecto del codificador, un ruido rosa a -16 LUFS salió a -15,3 (medido)."""
    suffix = Path(out).suffix.lower()
    if suffix in ('.mp4', '.mov', '.mkv', '.m4a'):
        return ['-c:a', 'aac', '-b:a', '192k']
    if suffix == '.webm':
        return ['-c:a', 'libopus', '-b:a', '160k']
    if suffix == '.mp3':
        return ['-c:a', 'libmp3lame', '-b:a', '192k']
    return []  # WAV, FLAC y el resto: su códec por defecto es sin pérdida


def measure(path: Path | str) -> dict:
    """I (LUFS), TP (dBTP) y LRA (LU) medidos con `ebur128`, no con los números que imprime loudnorm."""
    report = ff.ffmpeg('-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-')
    lufs, peak = ff.parse_loudness(report)
    lra = re.search(r'^\s*LRA:\s+(-?[\d.]+) LU', report, re.M)
    if lra is None:
        raise ValueError('ffmpeg printed no loudness range')
    return {'I': lufs, 'TP': peak, 'LRA': float(lra[1])}


def reference_error(source: Path | str) -> dict | None:
    """El error de una ruta que no se normaliza: lo que está en `reference/` son referencias de clonación."""
    if Path(source).resolve().is_relative_to(paths.references_dir().resolve()):
        return {'code': 'reference_protected', 'params': {}}
    return None


def normalize(source: Path | str, out: Path | str, *, target: float, enhance: bool = False) -> dict:
    """Normaliza el audio de `source` a `target` LUFS en dos pasadas y escribe `out`.

    Devuelve lo medido antes y después, el modo con el que loudnorm terminó (`linear` o `dynamic`) y el objetivo.
    """
    source = Path(source)
    before = measure(source)
    first = ff.json_loudnorm(
        ff.ffmpeg('-i', str(source), '-map', '0:a:0', '-af', first_pass(target, enhance), '-f', 'null', '-')
    )
    report = ff.ffmpeg(
        '-y',
        '-i',
        str(source),
        '-map',
        '0:v?',
        '-c:v',
        'copy',
        '-map',
        '0:a:0',
        '-af',
        second_pass(first, target, enhance),
        *audio_args(out),
        str(out),
    )
    mode = re.search(
        r'Normalization type:\s+(\w+)', report, re.IGNORECASE
    )  # loudnorm lo escribe «Type» con T mayúscula
    return {
        'before': before,
        'after': measure(out),
        'mode': mode[1].lower() if mode else 'unknown',
        'target': target,
    }


def build_parser() -> argparse.ArgumentParser:
    """Los flags del servicio: --input, --out, --preset, --target, --enhance y --report."""
    parser = argparse.ArgumentParser(prog='normalize', description='Normalize the loudness of a file to LUFS.')
    parser.add_argument('--input', required=True, help='audio or video to normalize')
    parser.add_argument('--out', required=True, help='normalized file, same kind as the input')
    parser.add_argument('--preset', required=True, choices=PRESETS, help='loudness target preset')
    parser.add_argument('--target', type=float, help='target LUFS, with the custom preset')
    parser.add_argument('--enhance', action='store_true', help='voice clean-up chain before loudnorm')
    parser.add_argument('--report', required=True, help='JSON with before, after, mode and target')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: normaliza y escribe el reporte en JSON."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.preset == 'custom' and args.target is None:
        parser.error('--target is required with the custom preset')
    report = normalize(args.input, args.out, target=target_lufs(args.preset, args.target), enhance=args.enhance)
    Path(args.report).write_text(json.dumps(report), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
