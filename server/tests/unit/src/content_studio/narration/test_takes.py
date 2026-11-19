"""Toma regenerada (spec 006, AC-3): rehace un bloque, copia los demás tal cual y no toca la original."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from content_studio.narration import takes


def _digests(folder: Path) -> dict[str, str]:
    """SHA-256 de cada archivo de la carpeta, con su ruta relativa en formato POSIX."""
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob('*'))
        if p.is_file()
    }


def test_ac3_regenerating_one_block_copies_the_others_and_keeps_the_original(tmp_path, fake_engine, narrated):
    original = narrated(tmp_path / 'original')
    before = _digests(original)

    takes.regenerate_take(fake_engine, original, index=1, seed=9, out_dir=tmp_path / 'take')

    take = _digests(tmp_path / 'take')
    assert _digests(original) == before
    assert take['blocks/0.wav'] == before['blocks/0.wav']
    assert take['blocks/2.wav'] == before['blocks/2.wav']
    assert take['blocks/1.wav'] != before['blocks/1.wav']
    script = json.loads((tmp_path / 'take' / 'script.json').read_text(encoding='utf-8'))
    assert [b['seed'] for b in script['blocks']] == [7, 9, 7]
    assert script['seeds'] == [7, 9]
    assert (tmp_path / 'take' / 'fake-expert.wav').exists()
