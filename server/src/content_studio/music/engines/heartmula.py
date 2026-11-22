"""HeartMuLa 3B (Apache 2.0): solo recibe tags, sin tonalidad, BPM ni compás.

Corre en server/data/music/.venv-heartmula."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from content_studio import paths
from content_studio.common import progress
from content_studio.music.duration import finish, plan_duration
from content_studio.music.engines.base import Jobs, MusicEngine


def download(checkpoints: Path) -> None:
    """Descarga los pesos de HeartMuLa desde Hugging Face."""
    from huggingface_hub import snapshot_download

    for repo, sub in [
        ('HeartMuLa/HeartMuLaGen', ''),
        ('HeartMuLa/HeartMuLa-oss-3B-happy-new-year', 'HeartMuLa-oss-3B'),
        ('HeartMuLa/HeartCodec-oss-20260123', 'HeartCodec-oss'),
    ]:
        snapshot_download(repo, local_dir=checkpoints / sub)  # reanuda y salta lo ya bajado


class HeartMuLa(MusicEngine):
    """Motor HeartMuLa (música)."""

    def generate(self, jobs: Jobs, a: argparse.Namespace) -> None:
        """Genera las pistas con HeartMuLa."""
        import soundfile as sf
        import torch
        import torchaudio
        from heartlib import HeartMuLaGenPipeline

        # torchaudio 2.10 guarda vía torchcodec, que choca con el CUDA de este torch.
        torchaudio.save = lambda path, wav, sr: sf.write(path, wav.T.numpy(), sr)
        # heartlib usa torch.compile, que necesita triton (no existe en Windows) y falla recién al generar.
        if importlib.util.find_spec('triton') is None:
            torch._dynamo.config.disable = True
        checkpoints = paths.engine_root('music', self.spec.venv, self.spec.name) / 'models' / 'heartmula-ckpt'
        download(checkpoints)
        # lazy_load: carga HeartMuLa, la descarga y recién ahí carga el codec (pico ~6 GB).
        pipe = HeartMuLaGenPipeline.from_pretrained(
            str(checkpoints),
            # cspell:ignore mula: nombre del componente de HeartMuLa en su API, no una palabra del código
            device={'mula': torch.device('cuda'), 'codec': torch.device('cuda')},
            dtype={'mula': torch.bfloat16, 'codec': torch.float32},
            version='3B',
            lazy_load=True,
        )
        # Con un solo [Instrumental] corta a ~12 s; una sección cada ~20 s lo estira hasta el tope.
        sections = ['[Intro]'] + ['[Instrumental]'] * max(1, int(a.duration // 20)) + ['[Outro]']
        for n, (style, output) in enumerate(jobs, 1):
            progress.emit((n - 1) / len(jobs), f'track {n}/{len(jobs)}')
            with torch.no_grad():
                pipe(
                    {'lyrics': '\n\n'.join(sections), 'tags': style['tags'] + ',instrumental'},
                    max_audio_length_ms=int(plan_duration(a.duration, self.spec.max_seconds) * 1000),
                    save_path=str(output),
                    topk=50,
                    temperature=1.0,
                    cfg_scale=1.5,
                )
            remaining = finish(output, a.duration)
            print(f'{output} ({remaining:.1f} s after trimming silence)')
