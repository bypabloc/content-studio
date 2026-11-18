"""Música instrumental local con ACE-Step 1.5 o HeartMuLa 3B, para GPU de 8 GB.

Uso:
    python music/musica.py --modelo acestep --estilo lofi-chill --duracion 60
    python music/musica.py --modelo acestep --duracion 30 --estilo corporate future-bass
    python music/musica.py --modelo acestep --duracion 30 --tono "E Minor" --bpm 105 \
        --estilo "synthwave, retro 80s, driving arpeggios"

--estilo acepta varios valores: un preset (ver ESTILOS) o texto libre, que se usa
tal cual como descripción. Cada preset define tonalidad, BPM y compás; el texto
libre los exige con --tono y --bpm. Estos flags también pisan los del preset.
El modelo se carga una vez y sale un .wav por estilo en --carpeta (out/music/
por defecto), con el silencio final ya recortado. Siempre instrumental. Los
pesos se descargan solos la primera vez a music/models/. Cada modelo corre en
su propio venv: music/.venv-acestep / music/.venv-heartmula (ver music/README.md).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content_studio import rutas
from content_studio.music.estilos import ESTILOS
from content_studio.music.motores.registro import MODELOS

__all__ = ['ESTILOS', 'MODELOS', 'construir_parser']  # el CLI también lee los catálogos de aquí


def construir_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para preguntar los que faltan y mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--modelo', choices=MODELOS, required=True, help='acestep (recomendado) o heartmula (lento)')
    ap.add_argument(
        '--estilo',
        nargs='+',
        default=['lofi-chill'],
        help=f'uno o más de los {len(ESTILOS)} presets (music/ESTILOS.md) o texto libre entre comillas',
    )
    ap.add_argument('--duracion', type=float, default=60, help='segundos antes del recorte (ACE ≤600, HeartMuLa ≤240)')
    ap.add_argument('--tono', help='tonalidad, ej. "C Major", "A Minor" (obligatoria con texto libre)')
    ap.add_argument('--bpm', type=int, help='tempo 30–300 (obligatorio con texto libre)')
    ap.add_argument('--compas', choices=['2', '3', '4', '6'], help='2/4, 3/4, 4/4 o 6/8 (por defecto 4/4)')
    ap.add_argument('--sin-lm', action='store_true', help='ACE-Step sin el planificador LM 0.6B: ~3x más rápido')
    ap.add_argument('--carpeta', type=Path, default=rutas.OUT / 'music', help='por defecto out/music/')
    ap.add_argument(
        '--variantes',
        type=int,
        default=1,
        help='pistas por estilo (<modelo>-<estilo>-v1.wav ...); la melodía cambia en cada una',
    )
    ap.add_argument(
        '--evaluar',
        action='store_true',
        help='al final mide con demucs cuánta voz hay en cada pista y marca las que cantan (se quiere solo música)',
    )
    ap.add_argument(
        '--reintentos',
        type=int,
        default=0,
        help='con --evaluar: rondas en las que se regeneran solo las pistas con voz',
    )
    return ap
