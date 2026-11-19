"""main() de narration tts: valida en el python del usuario, se relanza en el venv del motor y narra cada guion.

Directo: PYTHONPATH=server/src python -m content_studio.narration.tts --model voxcpm2 --voice karen-savage --text "..."
Flags y formato del guion: content_studio/narration/parser.py.
"""

from __future__ import annotations

import random

from content_studio import paths
from content_studio.common import process
from content_studio.narration.metadata import notices_voice, save_metadata
from content_studio.narration.parser import ENGINES, STYLES, approved_voices, build_parser
from content_studio.narration.pipeline import batch_auto, evaluate, narrate
from content_studio.narration.script import plan, scripts, warn_overwrite


def main() -> None:
    ap = build_parser()
    a = ap.parse_args()
    if a.retries and not a.evaluate:
        ap.error('--retries needs --evaluate')
    if a.voice:
        sheet = approved_voices(STYLES)[a.voice]
        if sheet['language'] != a.language:
            ap.error(f'la voz {a.voice} es en "{sheet["language"]}": usa --language {sheet["language"]}')
        a.ref = paths.VOICES / a.voice

    jobs = plan(a, scripts(a))  # valida estilos y rutas antes de relanzar y de cargar el modelo

    e = ENGINES[a.model]
    # Desde aquí corre en el venv del motor: los avisos se imprimen una sola vez.
    process.use_venv(e.path_venv(), 'server/data/narration/README.md', module='content_studio.narration.tts')
    if a.voice:
        notices_voice(a.voice, approved_voices(STYLES)[a.voice])
    warn_overwrite(jobs)

    import torch

    engine = e.create()
    batch = a.batch or (batch_auto(torch.cuda.mem_get_info()[0] / 2**30, e.weights) if e.batch else 1)
    seed = a.seed if a.seed is not None else random.randrange(2**31)
    print(f'Seed: {seed}')
    if not e.commercial:
        print(f'Notice: {a.model} has a non-commercial license ({e.license}). Personal use only.')
    elif 'academic' in e.license:
        print(
            f'Notice: {a.model} is Apache-2.0, but its model card says "for academic purposes only" (unclear). '
            'Ver docs/research/voicestudio-narracion/07.'
        )

    results = [
        narrate(engine, text, style, a.ref, output, batch, seed, language=a.language, master=a.master, lufs=a.lufs)
        for text, style, output in jobs
    ]

    if a.evaluate:
        evaluate(engine, results, batch, seed, a.retries, a.language)
    elif engine.suggest_evaluate:
        print(f'Tip: use --evaluate with {a.model}')
    for g in results:
        save_metadata(engine, g)


if __name__ == '__main__':
    main()
