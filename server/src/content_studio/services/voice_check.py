"""Chequeo de una toma de voz propia (spec 010, D-3 y AC-4): bordes, pico, duración, pausas, ruido y texto.

Corre en la cola con el recurso gpu, porque whisper usa la GPU. El veredicto es `ok` o `retake`, y cada razón es una
clave del catálogo (`voice.check.<razón>`). El resultado queda junto a la toma, en `<n>.check.json`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from content_studio import messages
from content_studio.common import ffmpeg
from content_studio.narration import profiles, recording_kit
from content_studio.narration.evaluation.compare import compare, normalize

RESOURCE = 'gpu'  # whisper usa la GPU: un chequeo a la vez, con el candado
PEAK_RANGE = (-12.0, -6.0)  # dBFS de la guía (docs/scripts/README.md)
PEAK_TOLERANCE = 1.0  # dB por encima o por debajo del rango
DURATION_TOLERANCE = 0.5  # s por encima o por debajo del rango del estilo
EDGE = (0.2, 0.6)  # s de silencio en cada borde: la guía pide de 0,3 a 0,5, con margen
PAUSE_MAX = 1.0  # s: un silencio interno más largo es una pausa
NOISE_MAX = -50.0  # dBFS: el ruido de la sala antes de hablar
TEXT_ERRORS_MAX = 0.15  # palabras mal dichas por palabra del guion, como WER_MAX en voices/build.py


def validate(params: dict) -> list[dict]:
    """Errores como {'code', 'params'}: el perfil, el estilo y la toma tienen que existir."""
    profile, style = str(params.get('profile', '')), str(params.get('style', ''))
    take = params.get('take')
    if not profiles.exists(profile):
        return [{'code': 'unknown_profile', 'params': {'profile': profile}}]
    if style not in recording_kit.STYLES:
        return [{'code': 'unknown_style', 'params': {'style': style}}]
    if not (profiles.takes_dir(profile, style) / f'{take}.wav').is_file():
        return [{'code': 'take_not_found', 'params': {'take': take}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """El chequeo corre con el python del server. `output_dir` no hace falta: el resultado va junto a la toma."""
    args = ['--profile', params['profile'], '--style', params['style'], '--take', str(params['take'])]
    if params.get('source_rate'):
        args += ['--source-rate', str(params['source_rate'])]
    return [sys.executable, '-m', 'content_studio.services.voice_check', *args]


def _silence_edges(spans: list[tuple[float, float | None]], duration: float) -> tuple[float, float, list[float]]:
    """El silencio del borde inicial y del final, y la duración de cada pausa interna."""
    lead = trail = 0.0
    pauses: list[float] = []
    for start, end in spans:
        end = duration if end is None else end
        if start < 0.05:
            lead = end
        elif end > duration - 0.05:
            trail = end - start
        else:
            pauses.append(end - start)
    return lead, trail, pauses


def _text_errors(expected: str, heard: str) -> float:
    """Palabras mal dichas por palabra del guion: lo que oye whisper frente al texto exacto (compare.py)."""
    words = normalize(expected)
    misses = sum(max(len(exp.split()), len(got.split())) for _, exp, got in compare(words, normalize(heard)))
    return misses / max(len(words), 1)


def _texts(codes: list[str]) -> list[str]:
    """El texto de cada razón o aviso. Las claves van escritas completas para que el gate de i18n las vea en uso."""
    catalog = {
        'too_long': messages.t('voice.check.too_long'),
        'too_short': messages.t('voice.check.too_short'),
        'peak_high': messages.t('voice.check.peak_high'),
        'peak_low': messages.t('voice.check.peak_low'),
        'edges': messages.t('voice.check.edges'),
        'pause': messages.t('voice.check.pause'),
        'noise': messages.t('voice.check.noise'),
        'text': messages.t('voice.check.text'),
        'whisper_missing': messages.t('voice.check.whisper_missing'),
    }
    return [catalog[code] for code in codes]


def check_take(path: Path, style: str, expected: str, transcribe: Callable[[Path], str | None]) -> dict:
    """Mide la toma y devuelve {verdict, reasons, notes, messages, measures}. `transcribe` dice lo que oye whisper
    (None si el comando no está instalado)."""
    low, high = next(item['duration'] for item in recording_kit.kit() if item['style'] == style)
    duration = ffmpeg.probe_duration(path)
    peak = ffmpeg.peak_dbfs(path)
    lead, trail, pauses = _silence_edges(ffmpeg.silences(path), duration)
    room = ffmpeg.room_tone_dbfs(path)
    reasons: list[str] = []
    if duration > high + DURATION_TOLERANCE:
        reasons.append('too_long')
    elif duration < low - DURATION_TOLERANCE:
        reasons.append('too_short')
    if peak > PEAK_RANGE[1] + PEAK_TOLERANCE:
        reasons.append('peak_high')
    elif peak < PEAK_RANGE[0] - PEAK_TOLERANCE:
        reasons.append('peak_low')
    if not all(EDGE[0] <= edge <= EDGE[1] for edge in (lead, trail)):
        reasons.append('edges')
    if any(length > PAUSE_MAX for length in pauses):
        reasons.append('pause')
    if room > NOISE_MAX:
        reasons.append('noise')
    notes: list[str] = []
    heard = transcribe(path)
    if heard is None:
        notes.append('whisper_missing')
    elif _text_errors(expected, heard) > TEXT_ERRORS_MAX:
        reasons.append('text')
    return {
        'verdict': 'retake' if reasons else 'ok',
        'reasons': reasons,
        'notes': notes,
        'messages': _texts(reasons + notes),
        'measures': {
            'duration': round(duration, 2),
            'peak_dbfs': round(peak, 2),
            'lead_s': round(lead, 2),
            'trail_s': round(trail, 2),
            'pauses_s': [round(length, 2) for length in pauses],
            'room_dbfs': round(room, 1),
        },
    }


def whisper_text(path: Path) -> str | None:
    """Lo que oye whisper en la toma, en español; None si el comando `whisper` no está instalado."""
    if shutil.which('whisper') is None:
        return None
    from content_studio.narration.evaluation.review import WHISPER_MODEL  # review importa numpy: solo al chequear

    with tempfile.TemporaryDirectory() as folder:
        command = ['whisper', str(path), '--model', WHISPER_MODEL, '--language', 'es', '--output_format', 'txt']
        subprocess.run([*command, '--output_dir', folder], check=True, capture_output=True)
        return (Path(folder) / f'{path.stem}.txt').read_text(encoding='utf-8').strip()


def main(argv: list[str] | None = None) -> int:
    """Entrada del trabajo: mide la toma y escribe `<n>.check.json` junto a ella; imprime el mismo JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True)
    parser.add_argument('--style', required=True)
    parser.add_argument('--take', type=int, required=True)
    parser.add_argument('--source-rate', type=int)
    args = parser.parse_args(argv)
    take = profiles.takes_dir(args.profile, args.style) / f'{args.take}.wav'
    result = check_take(take, args.style, recording_kit.plain_text(args.style), whisper_text)
    if args.source_rate:  # la toma se remuestreó al subirla: el chequeo lo anota (spec 010, D-2)
        result['notes'].append('resampled')
        result['messages'].append(messages.t('voice.check.resampled'))
        result['measures']['source_rate'] = args.source_rate
    take.with_suffix('.check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
