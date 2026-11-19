"""Música instrumental local con ACE-Step 1.5 o HeartMuLa 3B, para GPU de 8 GB.

Uso:
    studio music --model acestep --style lofi-chill --duration 60
    studio music --model acestep --duration 30 --style corporate future-bass
    studio music --model acestep --duration 30 --key "E Minor" --bpm 105 \
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

SUMMARY = 'Local instrumental music with ACE-Step 1.5 or HeartMuLa 3B, for an 8 GB GPU.'

__all__ = ['STYLES', 'MODELS', 'build_parser']  # el CLI también lee los catálogos de aquí


def build_parser() -> argparse.ArgumentParser:
    """Flags del script. `studio` los usa para la ayuda y para validar antes de encolar."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', choices=MODELS, required=True, help='acestep (recommended) or heartmula (slow)')
    ap.add_argument(
        '--style',
        nargs='+',
        default=['lofi-chill'],
        help=f'one or more of the {len(STYLES)} presets (server/data/music/ESTILOS.md), or free text in quotes',
    )
    ap.add_argument('--duration', type=float, default=60, help='seconds before trimming (ACE ≤600, HeartMuLa ≤240)')
    ap.add_argument('--key', help='key, e.g. "C Major", "A Minor" (required with free text)')
    ap.add_argument('--bpm', type=int, help='tempo 30–300 (required with free text)')
    ap.add_argument('--time-signature', choices=['2', '3', '4', '6'], help='2/4, 3/4, 4/4 or 6/8 (default 4/4)')
    ap.add_argument('--no-lm', action='store_true', help='ACE-Step without the LM 0.6B planner: ~3x faster')
    ap.add_argument('--folder', type=Path, default=paths.OUT / 'music', help='default out/music/')
    ap.add_argument(
        '--variants',
        type=int,
        default=1,
        help='tracks per style (<model>-<style>-v1.wav ...); the melody changes in each one',
    )
    ap.add_argument(
        '--evaluate',
        action='store_true',
        help='at the end, measures with demucs how much voice each track has and flags the ones that sing '
        '(only music is wanted)',
    )
    ap.add_argument(
        '--retries',
        type=int,
        default=0,
        help='with --evaluate: rounds in which only tracks with voice are regenerated',
    )
    return ap
