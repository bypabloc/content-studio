"""ACE-Step 1.5 (MIT): DiT 2B turbo + planificador LM 0.6B, con offload para 8 GB.

Corre en server/data/music/.venv-acestep."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from content_studio import paths
from content_studio.common import progress
from content_studio.music.duration import finish, plan_duration
from content_studio.music.engines.base import Jobs, MusicEngine


class AceStep(MusicEngine):
    """Motor ACE-Step 1.5 (música)."""

    def generate(self, jobs: Jobs, a: argparse.Namespace) -> None:
        """Genera las pistas con ACE-Step."""
        repo = paths.engine_root('music', self.spec.venv, self.spec.name) / 'models' / 'ACE-Step-1.5'
        os.environ['ACESTEP_PROJECT_ROOT'] = str(repo)
        from acestep.handler import AceStepHandler
        from acestep.inference import GenerationConfig, GenerationParams, generate_music
        from acestep.llm_inference import LLMHandler
        from acestep.model_downloader import ensure_lm_model, ensure_main_model

        ckpt = repo / 'checkpoints'
        for ok, msg in [ensure_main_model(ckpt)] + ([] if a.no_lm else [ensure_lm_model('acestep-5Hz-lm-0.6B', ckpt)]):
            if not ok:
                sys.exit(msg)

        # Perfil 6-8 GB de la guía oficial: DiT 2B turbo + LM 0.6B (backend pt) con offload.
        dit = AceStepHandler()
        dit.initialize_service(
            project_root=str(repo),
            config_path='acestep-v15-turbo',
            device='cuda',
            offload_to_cpu=True,
        )
        llm = LLMHandler()
        if not a.no_lm:
            llm.initialize(
                checkpoint_dir=str(ckpt),
                lm_model_path='acestep-5Hz-lm-0.6B',
                backend='pt',
                device='cuda',
                offload_to_cpu=True,
            )

        # Con semilla fija (las muestras, spec 011), la misma en cada pista; sin ella, una semilla nueva por pista.
        seed = getattr(a, 'seed', None)
        config = GenerationConfig(
            batch_size=1,
            use_random_seed=seed is None,
            seeds=None if seed is None else [seed],
            audio_format='wav',
        )
        for n, (style, output) in enumerate(jobs, 1):
            progress.emit((n - 1) / len(jobs), f'track {n}/{len(jobs)}')
            params = GenerationParams(
                caption=style['caption'],
                lyrics='[Instrumental]',
                instrumental=True,
                bpm=style['bpm'],
                keyscale=style['key'],
                timesignature=style['time_signature'],
                duration=plan_duration(a.duration, self.spec.max_seconds),
                thinking=not a.no_lm,
            )
            r = generate_music(dit, llm, params, config, save_dir=str(output.parent))
            if not r.success:
                print(f'ACE-Step failed on {output.name}: {r.error}')
                continue
            Path(r.audios[0]['path']).replace(output)
            remaining = finish(output, a.duration)
            print(f'{output} ({remaining:.1f} s after trimming silence; {style["key"]}, {style["bpm"]} BPM)')
