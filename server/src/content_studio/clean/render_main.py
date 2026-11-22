"""Render final del limpiador (spec 013, D-4 y D-5): el archivo limpio, las exportaciones y el informe.

Corre en el venv principal: es ffmpeg y texto, sin modelos.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from content_studio.clean import cuts, exports
from content_studio.clean.plan import keep_segments
from content_studio.clean.render import render_audio, render_video
from content_studio.common import ffmpeg as ff
from content_studio.media import formats

AUDIO_FPS = 25.0  # las exportaciones de solo audio usan 25 cuadros, como el EDL de la spec


def _fps(source: Path) -> float:
    """Tasa de cuadros del video como número: ffprobe da fracciones como «30000/1001»."""
    rate = ff.frame_rate(source)
    if '/' in rate:
        numerator, denominator = rate.split('/')
        return int(numerator) / int(denominator)
    return float(rate)


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
        render_video(source, keep, clean, nvenc=_nvenc(nvenc))
        fps = _fps(source)
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
