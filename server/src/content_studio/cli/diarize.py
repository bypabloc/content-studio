"""Subcomando `studio diarize` (spec 035, AC-11): encola la diarización de un audio y muestra su carpeta."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from content_studio.cli import submit

MAX_SPEAKERS = 20  # el mismo límite que el servicio; aquí se revisa para dar el motivo en inglés


def run(args: argparse.Namespace, main_path: Path) -> int:
    """Encola la diarización con los hablantes pedidos. 0 si terminó, 1 si falló y 2 si la combinación no es válida."""
    counts = {}
    if args.speakers is not None:
        counts['num_speakers'] = args.speakers
    if args.min_speakers is not None:
        counts['min_speakers'] = args.min_speakers
    if args.max_speakers is not None:
        counts['max_speakers'] = args.max_speakers
    low, high = args.min_speakers, args.max_speakers
    out_of_range = any(not 1 <= value <= MAX_SPEAKERS for value in counts.values())
    if out_of_range or (low is not None and high is not None and low > high):
        print(
            f'The speaker counts must be between 1 and {MAX_SPEAKERS}, '
            'and --min-speakers cannot be greater than --max-speakers.',
            file=sys.stderr,
        )
        return 2
    return submit.run('diarize', {'input': str(args.input), **counts}, args.db, main_path)
