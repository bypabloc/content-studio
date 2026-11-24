"""Render final del limpiador (spec 013, D-4 y D-5): el archivo limpio, las exportaciones y el informe.

Corre en el venv principal: es ffmpeg y texto, sin modelos.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from content_studio.clean import cuts, exports
from content_studio.clean.plan import keep_segments
from content_studio.clean.render import frames_per_second, on_frame_grid, render_audio, render_video
from content_studio.media import formats

AUDIO_FPS = 25.0  # las exportaciones de solo audio usan 25 cuadros, como el EDL de la spec


def _nvenc(choice: bool | None) -> bool:
    """Codificador por equipo: NVENC si hay NVIDIA. Si `choice` viene dado, se respeta."""
    if choice is not None:
        return choice
    from content_studio.system import tools

    return tools.detect()['gpu'] is not None


def run(source: Path, analysis: Path, out: Path, *, nvenc: bool | None = None) -> dict:
    """Escribe en `out` el archivo limpio, la transcripción, SRT, EDL, XML y `report.json`; devuelve el informe."""
    started = time.monotonic()
    document = cuts.load(analysis)
    enabled = [cut for cut in document['cuts'] if cut['enabled']]
    duration = document['duration']
    keep = keep_segments(enabled, duration)
    out.mkdir(parents=True, exist_ok=True)

    if formats.is_video(source):
        clean = out / 'clean.mp4'
        fps = frames_per_second(source)
        keep = on_frame_grid(keep, fps)  # el video corta en cuadros: informe y exportaciones usan esos mismos tiempos
        render_video(source, keep, clean, nvenc=_nvenc(nvenc))
    else:
        clean = out / 'clean.wav'
        render_audio(source, keep, clean)
        fps = AUDIO_FPS

    transcript = json.loads(Path(document['transcript']).read_text(encoding='utf-8'))
    words = [word for segment in transcript['segments'] for word in segment['words']]
    (out / 'transcript.txt').write_text(exports.transcript_txt(transcript['segments']), encoding='utf-8')
    (out / 'transcript.json').write_text(
        json.dumps(exports.transcript_json(words, enabled), ensure_ascii=False, indent=2), encoding='utf-8'
    )
    (out / 'subtitles.srt').write_text(exports.srt(words, enabled), encoding='utf-8')
    (out / 'cuts.edl').write_text(exports.edl(keep, fps=fps), encoding='utf-8')
    (out / 'cuts.xml').write_text(
        exports.xml_sequence(keep, fps, str(source.resolve()), name=source.stem, duration=duration), encoding='utf-8'
    )
    report = exports.report(
        duration_before=duration,
        keep=keep,
        cuts=enabled,
        model=document['model'],
        language=document['language'],
        process_seconds=time.monotonic() - started,
    )
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def build_parser() -> argparse.ArgumentParser:
    """Los flags de `clean.render`: el original, la carpeta del análisis y la salida del trabajo."""
    parser = argparse.ArgumentParser(prog='render_main', description='Render the clean file, exports and report.')
    parser.add_argument('--input', required=True, help='the original audio or video')
    parser.add_argument('--analysis', required=True, help='folder of the analysis, with its cuts.json')
    parser.add_argument('--out', required=True, help='output folder of the job')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: renderiza y deja el informe en stdout. Corre sin modelos, así que no relanza venv."""
    args = build_parser().parse_args(argv)
    report = run(Path(args.input), Path(args.analysis), Path(args.out))
    print(json.dumps(report), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
