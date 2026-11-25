"""Diarización con pyannote: quién habla y cuándo, con sus turnos y embeddings (spec 035, D-2).

Corre en `.venv-diarize`: pyannote, torch y numpy se importan dentro de las funciones, así `--help` no los necesita.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from content_studio import paths
from content_studio.common import process
from content_studio.common import progress as progress_protocol
from content_studio.diarization import exports
from content_studio.engines import recipes

README = 'server/src/content_studio/engines/recipes/pyannote.json'
EMBEDDING_BATCH = 4
STEP_SPANS = {'segmentation': (0.0, 0.5), 'embeddings': (0.5, 0.95)}
SPEAKER_FLAGS = {'num_speakers': '--speakers', 'min_speakers': '--min-speakers', 'max_speakers': '--max-speakers'}


def build_parser() -> argparse.ArgumentParser:
    """Los flags del servicio: --input (WAV de 16 kHz mono), --out y el número de hablantes."""
    parser = argparse.ArgumentParser(prog='diarize_main', description='Diarize an audio file with pyannote.')
    parser.add_argument('--input', required=True, help='16 kHz mono WAV to diarize')
    parser.add_argument('--out', required=True, help='folder for turns.json, speakers.json and embeddings.json')
    parser.add_argument('--speakers', type=int, help='exact number of speakers')
    parser.add_argument('--min-speakers', type=int, help='lowest number of speakers to look for')
    parser.add_argument('--max-speakers', type=int, help='highest number of speakers to look for')
    return parser


def speaker_counts(args: argparse.Namespace) -> dict[str, int]:
    """Lo que pyannote recibe del número de hablantes: uno exacto, un rango o nada (automático)."""
    if args.speakers is not None:
        return {'num_speakers': args.speakers}
    counts = {}
    if args.min_speakers is not None:
        counts['min_speakers'] = args.min_speakers
    if args.max_speakers is not None:
        counts['max_speakers'] = args.max_speakers
    return counts


def available() -> bool:
    """¿Está instalado el venv de pyannote? Sin él no hay diarización (spec 035, AC-7)."""
    return _venv().is_dir()


def pipeline_input(source: Path) -> tuple[dict[str, Any], float]:
    """El dict que pyannote recibe: la forma de onda (1, n) float32 y sample_rate; y la duración en segundos."""
    import wave

    import numpy as np
    import torch

    with wave.open(str(source), 'rb') as handle:
        rate = handle.getframerate()
        frames = handle.getnframes()
        raw = handle.readframes(frames)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return {'waveform': torch.from_numpy(samples.reshape(1, -1)), 'sample_rate': rate}, frames / rate


def load_pipeline(model: Path) -> Any:
    """El pipeline de community-1 desde su carpeta local, en GPU si la hay, con lote 4 para los embeddings."""
    import torch
    from pyannote.audio import Pipeline  # solo existe en .venv-diarize

    pipeline = Pipeline.from_pretrained(str(model))
    if torch.cuda.is_available():
        pipeline.to(torch.device('cuda'))
    pipeline.embedding_batch_size = EMBEDDING_BATCH
    return pipeline


def progress_hook(
    step: str, _artifact: Any, file: Any = None, total: int | None = None, completed: int | None = None
) -> None:
    """Traduce las etapas de pyannote a fracciones del progreso: segmentación de 0 a 0,5 y embeddings de 0,5 a 0,95."""
    span = STEP_SPANS.get(step)
    if span is None:
        return
    if total is None or completed is None:
        progress_protocol.emit(span[0], step)
        return
    progress_protocol.emit(progress_protocol.span_fraction(span, completed, total), step)


def turns_of(annotation: Any) -> list[dict[str, Any]]:
    """Los turnos de una anotación de pyannote como {start, end, speaker}, en orden de tiempo."""
    return [
        {'start': round(segment.start, 3), 'end': round(segment.end, 3), 'speaker': label}
        for segment, _, label in annotation.itertracks(yield_label=True)
    ]


def diarize(source: Path, model: Path, out: Path, counts: dict[str, int]) -> dict[str, Any]:
    """Corre pyannote sobre `source`, escribe la carpeta `out` y devuelve el resultado."""
    audio, duration = pipeline_input(source)
    output = load_pipeline(model)(audio, hook=progress_hook, **counts)
    labels = output.speaker_diarization.labels()
    result: dict[str, Any] = {
        'duration': round(duration, 3),
        'speakers': labels,
        'diarization': turns_of(output.speaker_diarization),
        'exclusive_diarization': turns_of(output.exclusive_speaker_diarization),
        'embeddings': {},
    }
    if output.speaker_embeddings is not None:
        result['embeddings'] = dict(zip(labels, output.speaker_embeddings.tolist(), strict=True))
    exports.write_result(out, result)
    return result


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: relanza en `.venv-diarize`, fija el entorno offline y diariza el WAV."""
    process.use_venv(_venv(), README, module='content_studio.diarization.diarize_main')
    args = build_parser().parse_args(argv)
    os.environ['PYANNOTE_METRICS_ENABLED'] = '0'
    os.environ['HF_HUB_OFFLINE'] = '1'
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    diarize(Path(args.input), _model_dir(), out, speaker_counts(args))
    return 0


def _venv() -> Path:
    """El venv de la receta `pyannote` (su carpeta la decide `paths.engine_root`)."""
    recipe = recipes.load('pyannote')
    return paths.engine_root(recipe.family, recipe.venv, recipe.engine) / recipe.venv


def _model_dir() -> Path:
    """La carpeta local de community-1: la receta la instala en `models/community-1`, y pyannote la carga sin red."""
    recipe = recipes.load('pyannote')
    return paths.engine_root(recipe.family, recipe.venv, recipe.engine) / 'models' / 'community-1'


if __name__ == '__main__':
    raise SystemExit(main())
