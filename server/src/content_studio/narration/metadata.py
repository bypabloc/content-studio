"""El .json de cada toma (lo necesario para reproducirla) y los avisos de licencia de las voces del catálogo."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

from content_studio import paths
from content_studio.narration.engines.base import TTSEngine
from content_studio.narration.voices.catalog import catalog, mention


def notices_voice(name: str, sheet: dict) -> None:
    """Lo que hay que saber antes de publicar una narración con una voz del catálogo: permiso del dueño y mención."""
    if not sheet.get('consent'):
        print(
            f'Notice: the voice {name} ({sheet["source"]}) has license {sheet["license"]}, but its owner did not give '
            'permission to clone it (rule 5 of AGENTS.md). Personal use only; for commercial use, ask for permission '
            'or use '
            'a voice with consent. See docs/research/voces-libres-clonacion/02.'
        )
    if m := mention(sheet):
        print(f'REQUIRED CREDIT ({sheet["license"]}): put this credit in the video description. It stays in the .json.')
        print(f'  {m}')
    if 'BY-SA' in sheet['license']:
        print(
            'Notice: "share alike" license (BY-SA). Do not put the original clip in the video, and if someone '
            'considers the narration an adaptation, it would have to be published under the same license. See '
            'docs/research/voces-libres-clonacion/12.'
        )


def voice_from_reference(ref: Path) -> dict | None:
    """Ficha del catálogo de la voz a la que pertenece una referencia
    (server/data/narration/voices/<voz>/<estilo>.wav), o None."""
    ref = Path(ref).resolve()
    if ref.parent.parent != paths.VOICES.resolve():
        return None
    sheet = catalog().get(ref.parent.name)
    return sheet and {'voice': ref.parent.name, 'license': sheet['license'], 'source': sheet['source'],
                      'consent': sheet.get('consent', False), 'mention': mention(sheet)}  # fmt: skip


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def version_tts() -> str:
    """Commit del script; con '-dirty' si hay cambios sin confirmar (la toma no sería reproducible con ese commit)."""
    r = subprocess.run(
        ['git', 'describe', '--always', '--dirty', '--abbrev=7'], cwd=paths.ROOT, capture_output=True, text=True
    )
    return r.stdout.strip() or 'unknown'


def save_metadata(engine: TTSEngine, g: dict) -> None:
    """Escribe <salida>.json con lo necesario para reproducir la toma: motor, semillas, referencias y bloques."""
    import torch

    e = engine.spec
    hashes: dict[Path, str] = {}
    blocks = []
    for i, (b, pb, (_, ini, end)) in enumerate(zip(g['secs'], g['pb'], g['blocks'], strict=False)):
        if pb['ref'] not in hashes:
            hashes[pb['ref']] = sha256(pb['ref'])
        blocks.append({
            'i': i + 1, 'text_script': b['text'], 'text_sent': pb['send'], 'style': pb['style'],
            'reference': str(pb['ref']), 'reference_sha256': hashes[pb['ref']],
            'emotion': pb['emotion'], 'mode': pb['mode'], 'pause_after': b['pause'],
            'start_s': round(ini, 3), 'end_s': round(end, 3), 'seed': g['seed_block'][i],
            'notices': pb['notices'],
        })  # fmt: skip
    meta = {
        'version_tts': version_tts(), 'date': datetime.now().astimezone().isoformat(timespec='seconds'),
        'engine': e.name, 'license': e.license, 'commercial': e.commercial, 'language': g['language'],
        'seed': g['seed'], 'seeds_por_round': g['seeds'], 'blocks': blocks,
        'master': g['master_info'], 'evaluation': g.get('evaluation'),
        'params': {**g['p'], **engine.params},
        'time_generation_s': round(g['time_s'], 1), 'duration_s': round(g['blocks'][-1][2], 2),
        'vram_peak_gib': round(torch.cuda.max_memory_reserved() / 2**30, 2),
        # Voces del catálogo usadas en la toma, con la mención que pide su licencia (para la descripción del video).
        'voices': list({v['voice']: v for pb in g['pb'] if (v := voice_from_reference(pb['ref']))}.values()) or None,
    }  # fmt: skip
    g['output'].with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
