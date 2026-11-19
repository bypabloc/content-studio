"""main() de music: valida en el python del usuario, se relanza en el venv del motor y genera las pistas.

Directo: PYTHONPATH=server/src python -m content_studio.music.music_main --model acestep --style lofi-chill
"""

from __future__ import annotations

import re
import sys
import unicodedata

from content_studio.common import process, progress
from content_studio.music.engines.base import Jobs
from content_studio.music.evaluation import free_gpu, with_voice
from content_studio.music.parser import MODELS, STYLES, build_parser


def resolve_style(
    value: str, key: str | None = None, bpm: int | None = None, time_signature: str | None = None
) -> tuple[str, dict]:
    """Devuelve (nombre de archivo, estilo). Los flags pisan los metadatos del preset;
    el texto libre sirve de caption y de tags, y exige tono y bpm.

    >>> resolve_style('ambient')[1]['key'], resolve_style('ambient', key='Am', bpm=60)[1]['bpm']
    ('D Major', 60)
    >>> name, e = resolve_style('Synthwave, retro 80s!', key='E Minor', bpm=105)
    >>> name, e['tags'], e['key'], e['bpm'], e['time_signature']
    ('synthwave-retro-80s', 'Synthwave, retro 80s!', 'E Minor', 105, '4')
    >>> resolve_style('Música épica', key='C Major', bpm=90)[0], resolve_style('¡¿?!', key='C Major', bpm=90)[0]
    ('musica-epica', 'free')
    >>> resolve_style('bossa nova')
    Traceback (most recent call last):
    SystemExit: "bossa nova" no es un preset: define --key y --bpm (ej. --key "C Major" --bpm 90)
    """
    if value in STYLES:
        name, base = value, STYLES[value]
    else:
        if key is None or bpm is None:
            sys.exit(f'"{value}" no es un preset: define --key y --bpm (ej. --key "C Major" --bpm 90)')
        ascii_ = unicodedata.normalize('NFKD', value.lower()).encode('ascii', 'ignore').decode()  # música → musica
        name = re.sub(r'[^a-z0-9]+', '-', ascii_).strip('-')[:60] or 'free'
        base = dict(caption=value, tags=value, time_signature='4')
    overwrite = {k: v for k, v in dict(key=key, bpm=bpm, time_signature=time_signature).items() if v is not None}
    return name, {**base, **overwrite}


def main() -> None:
    """Entrada de `python -m content_studio.music.music_main`."""
    process.console_utf8()  # cp1252 (Windows, a una tubería) no tiene ≤ ni –: que no reviente el --help
    ap = build_parser()
    a = ap.parse_args()
    spec = MODELS[a.model]
    if a.retries and not a.evaluate:
        ap.error('--retries needs --evaluate')
    if a.evaluate and not spec.evaluates:
        ap.error('--evaluate only works in the acestep venv (demucs lives there)')
    if a.variants < 1:
        ap.error('--variants must be 1 or more')

    # Validar antes de relanzar en el venv y cargar el modelo.
    jobs = []
    for value in a.style:
        name, style = resolve_style(value, a.key, a.bpm, a.time_signature)
        for i in range(1, a.variants + 1):
            suffix = f'-v{i}' if a.variants > 1 else ''
            jobs.append((style, (a.folder / f'{a.model}-{name}{suffix}.wav').resolve()))

    process.use_venv(spec.path_venv(), 'server/data/music/README.md', module='content_studio.music.music_main')
    a.folder.mkdir(parents=True, exist_ok=True)
    engine = spec.create()

    def generate(items: Jobs) -> None:
        for _, output in items:  # si el motor falla, no queda la pista de una corrida anterior como si fuera nueva
            output.unlink(missing_ok=True)
        engine.generate(items, a)

    progress.emit(0, 'start')
    generate(jobs)
    progress.emit(1, 'done')
    if not a.evaluate:
        missing = [s.name for _, s in jobs if not s.exists()]
        if missing:
            sys.exit(f'Not generated: {", ".join(missing)}')
        return

    free_gpu()
    pending = with_voice([t[1] for t in jobs])
    for _ in range(a.retries):
        if not pending:
            break
        print(f'Regenerating {len(pending)} track(s) with voice...', flush=True)
        generate([t for t in jobs if t[1] in pending])
        free_gpu()
        pending = with_voice(pending)
    print(f'{len(jobs) - len(pending)}/{len(jobs)} tracks without voice')
    if pending:
        sys.exit(f'Still with voice after retries: {", ".join(p.name for p in pending)}')


if __name__ == '__main__':
    main()
