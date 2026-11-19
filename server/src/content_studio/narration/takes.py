"""Toma nueva a partir de otra (spec 006, D-2): rehace un bloque con su semilla y copia los demás tal cual."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from content_studio.narration.blocks import prepare_blocks
from content_studio.narration.engines.base import TTSEngine
from content_studio.narration.pipeline import regenerate
from content_studio.narration.styles import STYLES


def regenerate_take(engine: TTSEngine, source: Path, index: int, seed: int, out_dir: Path) -> dict:
    """Escribe en `out_dir` una toma nueva de `source`: el bloque `index` con la semilla `seed` y los demás bloques
    copiados byte a byte, para que su hash no cambie. La toma original no se toca. Devuelve el estado `g`."""
    import soundfile as sf

    data = json.loads((source / 'script.json').read_text(encoding='utf-8'))
    ref, secs = Path(data['ref']), data['segments']
    pb = prepare_blocks(engine, secs, ref)
    (out_dir / 'blocks').mkdir(parents=True, exist_ok=True)
    audios: list = [None] * len(secs)
    sr = 0
    for i in range(len(secs)):
        if i != index:
            shutil.copyfile(source / 'blocks' / f'{i}.wav', out_dir / 'blocks' / f'{i}.wav')
            audios[i], sr = sf.read(source / 'blocks' / f'{i}.wav', dtype='float32')
    g = dict(
        output=out_dir / data['wav'], ref=ref, secs=secs, pb=pb, style=data['style'], p=STYLES[data['style']],
        language=data['language'], seed=data['seed'], seeds=list(data['seeds']),
        seed_block=[b['seed'] for b in data['blocks']], audios=audios, sr=sr, blocks=[], time_s=0.0,
        master=data['master'], lufs=data['lufs'], master_info=None,
    )  # fmt: skip
    regenerate(engine, g, [index], batch=1, seed=seed)
    return g
