"""Pipeline de narración: lo que deja cada toma en su carpeta (spec 006, AC-2)."""

from __future__ import annotations

import json

import numpy as np
import soundfile as sf

from content_studio.narration import pipeline
from content_studio.narration.engines.base import EngineSpec, TTSEngine

SR = 8000
TEXT = 'Uno, dos y tres.\n\nCuatro, cinco y seis.\n\nSiete, ocho y nueve.'


class FakeEngine(TTSEngine):
    """Motor sin GPU: cada bloque es ruido determinista de 0,4 s."""

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        audios = [
            np.random.default_rng(len(b['send'])).normal(0, 0.1, int(SR * 0.4)).astype(np.float32) for b in blocks
        ]
        return audios, SR


def fake_spec() -> EngineSpec:
    return EngineSpec(
        name='fake', venv='', module='', kind='FakeEngine', license='MIT', commercial=True,
        txt=None, ref_max_s=30.0, repo='',
    )  # fmt: skip


def test_ac2_blocks_persisted(tmp_path, monkeypatch):
    """AC-2: el trabajo deja el .wav, blocks/0..n-1.wav y script.json con una semilla por bloque."""
    monkeypatch.setattr(pipeline, 'fix', lambda seed: None)  # la semilla de la GPU no es lo que se prueba
    monkeypatch.setattr(pipeline, 'peak_vram_gib', lambda: 0.0)  # sin CUDA no hay VRAM que informar
    ref = tmp_path / 'ref.wav'
    sf.write(ref, np.zeros(SR, dtype=np.float32), SR)
    job = tmp_path / 'job'

    pipeline.narrate(
        FakeEngine(fake_spec()), TEXT, 'expert', ref, job / 'fake-expert.wav', batch=1, seed=7, master='no'
    )

    assert (job / 'fake-expert.wav').exists()
    assert sorted(p.name for p in (job / 'blocks').iterdir()) == ['0.wav', '1.wav', '2.wav']
    for i in range(3):
        block, sr = sf.read(job / 'blocks' / f'{i}.wav', dtype='float32')
        assert sr == SR and len(block) > 0
    script = json.loads((job / 'script.json').read_text(encoding='utf-8'))
    assert [b['seed'] for b in script['blocks']] == [7, 7, 7]
    assert (script['style'], script['language'], script['master']) == ('expert', 'es', 'no')
