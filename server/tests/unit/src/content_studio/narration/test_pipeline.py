"""Pipeline de narración: lo que deja cada toma en su carpeta (spec 006, AC-2)."""

from __future__ import annotations

import json

import soundfile as sf


def test_ac2_blocks_persisted(tmp_path, narrated):
    """AC-2: el trabajo deja el .wav, blocks/0..n-1.wav y script.json con una semilla por bloque."""
    job = narrated(tmp_path / 'job')

    assert (job / 'fake-expert.wav').exists()
    assert sorted(p.name for p in (job / 'blocks').iterdir()) == ['0.wav', '1.wav', '2.wav']
    for i in range(3):
        block, sr = sf.read(job / 'blocks' / f'{i}.wav', dtype='float32')
        assert sr == 8000 and len(block) > 0
    script = json.loads((job / 'script.json').read_text(encoding='utf-8'))
    assert [b['seed'] for b in script['blocks']] == [7, 7, 7]
    assert (script['style'], script['language'], script['master']) == ('expert', 'es', 'no')
