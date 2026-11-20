"""Muestras de 10 s de cada preset, para el buscador (spec 011, D-3): un trabajo de la cola `music.samples`.

Corre en server/data/music/.venv-acestep, con ACE-Step sin el planificador LM y una semilla fija.
Solo genera las que faltan; `--force` las regenera todas.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content_studio import paths
from content_studio.common import process
from content_studio.music.engines.base import MusicEngine
from content_studio.music.engines.registry import MODELS
from content_studio.music.styles import STYLES

SAMPLE_SECONDS = 10
SEED = 1234  # la misma para todas las muestras: regenerar una da el mismo clip
SAMPLES = paths.MUSIC / 'samples'


def pending(styles: list[str], folder: Path, force: bool) -> list[str]:
    """Los estilos cuya muestra falta; todos con `force`.

    >>> pending(['a', 'b'], Path('/no/existe'), False)
    ['a', 'b']
    """
    return [style for style in styles if force or not (folder / f'{style}.wav').is_file()]


def render_samples(engine: MusicEngine, styles: list[str], folder: Path, force: bool) -> list[str]:
    """Genera la muestra de los estilos que faltan y devuelve los que generó."""
    todo = pending(styles, folder, force)
    if not todo:
        return []
    folder.mkdir(parents=True, exist_ok=True)
    jobs = [(STYLES[style], folder / f'{style}.wav') for style in todo]
    for _, output in jobs:  # si el motor falla, no queda la muestra de una corrida anterior como si fuera nueva
        output.unlink(missing_ok=True)
    engine.generate(jobs, argparse.Namespace(duration=SAMPLE_SECONDS, no_lm=True, seed=SEED, evaluate=False))
    return todo


def main() -> None:
    """Entrada de `python -m content_studio.music.samples_main`, ya dentro del venv de ACE-Step."""
    process.console_utf8()
    ap = argparse.ArgumentParser(description='10-second sample of each music preset (ACE-Step, no LM, fixed seed).')
    ap.add_argument('--styles', nargs='+', default=list(STYLES), help='presets to sample (default: all)')
    ap.add_argument('--force', action='store_true', help='regenerate the samples that already exist')
    a = ap.parse_args()
    spec = MODELS['acestep']
    process.use_venv(spec.path_venv(), 'server/data/music/README.md', module='content_studio.music.samples_main')
    done = render_samples(spec.create(), a.styles, SAMPLES, a.force)
    print(f'{len(done)} sample(s) generated in {SAMPLES}', flush=True)


if __name__ == '__main__':
    main()
