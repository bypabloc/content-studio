"""Música instrumental local con ACE-Step 1.5 o HeartMuLa 3B, para GPU de 8 GB.

Uso:
    python cli.py music --model acestep --style lofi-chill --duration 60
    python cli.py music --model acestep --duration 30 --style corporate future-bass
    python cli.py music --model acestep --duration 30 --key "E Minor" --bpm 105 \
        --style "synthwave, retro 80s, driving arpeggios"

--style acepta varios valores: un preset (ver ESTILOS) o texto libre, que se usa
tal cual como descripción. Cada preset define tonalidad, BPM y compás; el texto
libre los exige con --key y --bpm. Estos flags también pisan los del preset.
El modelo se carga una vez y sale un .wav por estilo en --folder (out/music/
por defecto), con el silencio final ya recortado. Siempre instrumental. Los
pesos se descargan solos la primera vez a server/data/music/models/. Cada modelo corre en
su propio venv: server/data/music/.venv-acestep / server/data/music/.venv-heartmula (ver server/data/music/README.md).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content_studio import paths
from content_studio.music.engines.registry import MODELS
from content_studio.music.styles import STYLES

__all__ = ['STYLES', 'MODELS', 'build_parser']  # el CLI también lee los catálogos de aquí


def build_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para preguntar los que faltan y mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', choices=MODELS, required=True, help='acestep (recomendado) o heartmula (lento)')
    ap.add_argument(
        '--style',
        nargs='+',
        default=['lofi-chill'],
        help=f'uno o más de los {len(STYLES)} presets (server/data/music/ESTILOS.md) o texto libre entre comillas',
    )
    ap.add_argument('--duration', type=float, default=60, help='segundos antes del recorte (ACE ≤600, HeartMuLa ≤240)')
    ap.add_argument('--key', help='tonalidad, ej. "C Major", "A Minor" (obligatoria con texto libre)')
    ap.add_argument('--bpm', type=int, help='tempo 30–300 (obligatorio con texto libre)')
    ap.add_argument('--time-signature', choices=['2', '3', '4', '6'], help='2/4, 3/4, 4/4 o 6/8 (por defecto 4/4)')
    ap.add_argument('--no-lm', action='store_true', help='ACE-Step sin el planificador LM 0.6B: ~3x más rápido')
    ap.add_argument('--folder', type=Path, default=paths.OUT / 'music', help='por defecto out/music/')
    ap.add_argument(
        '--variants',
        type=int,
        default=1,
        help='pistas por estilo (<modelo>-<estilo>-v1.wav ...); la melodía cambia en cada una',
    )
    ap.add_argument(
        '--evaluate',
        action='store_true',
        help='al final mide con demucs cuánta voz hay en cada pista y marca las que cantan (se quiere solo música)',
    )
    ap.add_argument(
        '--retries',
        type=int,
        default=0,
        help='con --evaluate: rondas en las que se regeneran solo las pistas con voz',
    )
    return ap
