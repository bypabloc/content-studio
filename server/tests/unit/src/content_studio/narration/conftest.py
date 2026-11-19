"""Motor falso y fixtures de la narración: sin GPU, sin venv y sin ffmpeg (spec 006, AC-2 y AC-3)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from content_studio.narration import pipeline
from content_studio.narration.engines.base import EngineSpec, TTSEngine

SR = 8000
TEXT = 'Uno, dos y tres.\n\nCuatro, cinco y seis.\n\nSiete, ocho y nueve.'


class FakeEngine(TTSEngine):
    """Cada bloque es ruido determinista: depende de la semilla que fijó `fix` y del texto del bloque."""

    def __init__(self, spec: EngineSpec) -> None:
        super().__init__(spec)
        self.seed = 0

    def generate(self, blocks: list[dict], language: str) -> tuple[list, int]:
        audios = [
            np.random.default_rng([self.seed, len(b['send'])]).normal(0, 0.1, int(SR * 0.4)).astype(np.float32)
            for b in blocks
        ]
        return audios, SR


def fake_spec() -> EngineSpec:
    return EngineSpec(
        name='fake', venv='', module='', kind='FakeEngine', license='MIT', commercial=True,
        txt=None, ref_max_s=30.0, repo='',
    )  # fmt: skip


@pytest.fixture
def fake_engine(monkeypatch: pytest.MonkeyPatch) -> FakeEngine:
    """Motor falso con `fix` y la VRAM sustituidos: la semilla de cada ronda queda en `engine.seed`."""
    engine = FakeEngine(fake_spec())
    monkeypatch.setattr(pipeline, 'fix', lambda seed: setattr(engine, 'seed', seed))
    monkeypatch.setattr(pipeline, 'peak_vram_gib', lambda: 0.0)
    return engine


@pytest.fixture
def narrated(fake_engine: FakeEngine, tmp_path: Path) -> Callable[..., Path]:
    """Narra TEXT (tres párrafos, estilo expert, semilla 7) en la carpeta que se pide y la devuelve."""
    ref = tmp_path / 'ref.wav'
    sf.write(ref, np.zeros(SR, dtype=np.float32), SR)

    def run(job: Path, seed: int = 7) -> Path:
        pipeline.narrate(fake_engine, TEXT, 'expert', ref, job / 'fake-expert.wav', batch=1, seed=seed, master='no')
        return job

    return run
