"""Generación de un guion: narrar, regenerar bloques sueltos y evaluar con whisper (con reintentos)."""

from __future__ import annotations

import random
import shutil
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path

from content_studio.narration.audio import trim, write
from content_studio.narration.blocks import prepare_blocks
from content_studio.narration.engines.base import TTSEngine
from content_studio.narration.engines.registry import free_todo
from content_studio.narration.evaluation.review import review, save_blocks, seed_round, transcribe
from content_studio.narration.styles import EMOTIONS, STYLES
from content_studio.narration.text.segments import segments, tags

# VRAM de Qwen por encima de los pesos: ~1.15 GiB la primera frase de ~300
# letras y ~1.3 GiB cada frase extra del lote. Más de 4 no mejora en 8 GB.
GIB_FIRST, GIB_POR_PHRASE, MARGIN_GIB = 1.15, 1.3, 0.5
BATCH_MAX = 4
NO_VOICE = 'the engine produced no voice; if the paragraph ends without . ? ! (cut mid-sentence), add punctuation'


def batch_auto(free_gib: float, weights_gib: float) -> int:
    """Frases por pasada que caben en la VRAM libre.

    >>> batch_auto(7.9, 2.06), batch_auto(5.2, 2.06), batch_auto(7.9, 3.95), batch_auto(5.2, 3.95)
    (4, 2, 2, 1)
    """
    extra = free_gib - weights_gib - GIB_FIRST - MARGIN_GIB
    return max(1, min(BATCH_MAX, 1 + int(extra // GIB_POR_PHRASE)))


def batches(indices: list[int], tam: int, key: Callable[[int], object]) -> list[list[int]]:
    """Trozos de hasta `tam` índices consecutivos con la misma clave. Así Qwen agrupa por referencia.

    >>> batches([0, 1, 2, 3, 4], 2, lambda i: i // 3)
    [[0, 1], [2], [3, 4]]
    >>> batches([0, 1], 1, lambda i: 0)
    [[0], [1]]
    """
    out: list[list[int]] = []
    for i in indices:
        if out and len(out[-1]) < tam and key(out[-1][0]) == key(i):
            out[-1].append(i)
        else:
            out.append([i])
    return out


def fix(seed: int) -> None:
    """Fija las semillas de Python, numpy y torch. Se llama antes de cada bloque (o pasada de lote)."""
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def narrate(
    engine: TTSEngine,
    text: str,
    style: str,
    ref: Path,
    output: Path,
    batch: int,
    seed: int,
    language: str = 'es',
    master: str = 'voice',
    lufs: float = -16.0,
) -> dict:
    """Genera todos los bloques del texto y escribe el .wav. Devuelve lo necesario para evaluar,
    regenerar bloques sueltos y escribir los metadatos."""
    import torch

    secs = segments(text, style)
    if not secs:
        sys.exit('The text is empty.')
    for i, b in enumerate(secs):
        if b['style'] not in STYLES:
            sys.exit(f'Unknown style "{b["style"]}" in paragraph {i + 1}. Options: {", ".join(STYLES)}')
        if b['emotion'] and b['emotion'][0] not in EMOTIONS:
            sys.exit(f'Unknown emotion "{b["emotion"][0]}" in paragraph {i + 1}. Options: {", ".join(EMOTIONS)}')
        if b['emotion'] and not 0 <= b['emotion'][1] <= 1:
            sys.exit(f'The emotion intensity in paragraph {i + 1} must be between 0 and 1.')
    if odd := tags(text):
        print(f'Notice: the model will read aloud {", ".join(odd)}. See server/data/narration/docs/formato-guion.md.')
    pb = prepare_blocks(engine, secs, ref)
    for i, p_ in enumerate(pb):
        for a in p_['notices']:
            print(f'Notice: paragraph {i + 1}: {a}')

    g = dict(
        output=output, secs=secs, pb=pb, style=style, p=STYLES[style], language=language, seed=seed,
        seeds=[], seed_block=[None] * len(secs), audios=[], sr=0, blocks=[], time_s=0.0,
        master=master, lufs=lufs, master_info=None,
    )  # fmt: skip
    regenerate(engine, g, range(len(secs)), batch, seed)
    dur = g['blocks'][-1][2]
    print(
        f'{output} ({dur:.1f} s, {engine.spec.name}, {style}, batch {batch}) | '
        f'generation {g["time_s"]:.1f} s, {dur / g["time_s"]:.2f}x real time | '
        f'peak VRAM {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB',
        flush=True,
    )
    return g


def regenerate(engine: TTSEngine, g: dict, indices: Iterable[int], batch: int, seed: int) -> None:
    """(Re)genera los bloques indicados del guion `g` con la semilla de la ronda y reescribe su .wav.
    Qwen genera hasta `lote` bloques de la misma referencia por pasada; el resto de a uno."""
    import numpy as np

    tam = batch if engine.spec.batch else 1
    if not g['audios']:
        g['audios'] = [None] * len(g['secs'])
    g['seeds'].append(seed)
    t0 = time.perf_counter()
    for group in batches(list(indices), tam, lambda i: (g['pb'][i]['ref'], g['pb'][i]['p']['temperature'])):
        fix(seed)  # la semilla se fija antes de cada bloque o pasada (§4)
        audios, g['sr'] = engine.generate([g['pb'][i] for i in group], g['language'])
        for i, a_ in zip(group, audios, strict=False):
            g['audios'][i] = trim(np.asarray(a_, dtype=np.float32), g['sr'])
            g['seed_block'][i] = seed
            if not len(g['audios'][i]) and NO_VOICE not in g['pb'][i]['notices']:
                print(f'Notice: paragraph {i + 1}: {NO_VOICE}')
                g['pb'][i]['notices'].append(NO_VOICE)
    g['time_s'] += time.perf_counter() - t0
    write(g)


def evaluate(engine: TTSEngine, results: list[dict], batch: int, seed: int, retries: int, language: str) -> None:
    if not shutil.which('whisper'):
        sys.exit('The whisper command is missing (pip install openai-whisper); cannot evaluate.')
    report: dict[int, tuple[list[str], list[int]]] = {}  # guion -> (observaciones, bloques con error)
    pending = {k: list(range(len(g['secs']))) for k, g in enumerate(results)}  # guion -> bloques
    for round in range(retries + 1):  # noqa: B007  (ronda se usa después del bucle)
        free_todo()  # libera la VRAM para whisper
        transcribe([w for k, idx in pending.items() for w in save_blocks(results[k], idx)], language)
        for k in pending:
            report[k] = review(results[k])
        pending = {k: report[k][1] for k in pending if report[k][1]}
        if not pending or round == retries:
            break
        n = sum(map(len, pending.values()))
        print(f'Retry {round + 1}/{retries}: regenerating {n} paragraph(s) from {len(pending)} script(s)...')
        for k, idx in pending.items():
            regenerate(engine, results[k], idx, batch, seed_round(seed, round + 1))

    for k, g in enumerate(results):
        problems, failed = report[k]
        g['evaluation'] = {'rounds': round + 1, 'observations': problems, 'ok': not failed}
        print(f'{"REVIEW" if failed else "OK     "} {g["output"]}')
        for line in problems:
            print(f'          {line}')
    review_n = sum(bool(f) for _, f in report.values())
    print(f'{len(results) - review_n}/{len(results)} without errors (rhythm notices do not count).')
