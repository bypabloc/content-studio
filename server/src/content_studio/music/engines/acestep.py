"""ACE-Step 1.5 (MIT): DiT 2B turbo + planificador LM 0.6B, con offload para 8 GB.

Corre en server/data/music/.venv-acestep."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from content_studio import paths
from content_studio.music.engines.base import Jobs, MusicEngine
from content_studio.music.evaluation import trim_silence

ACE_REPO = paths.MUSIC / 'models' / 'ACE-Step-1.5'


class AceStep(MusicEngine):
    def generate(self, jobs: Jobs, a: argparse.Namespace) -> None:
        os.environ['ACESTEP_PROJECT_ROOT'] = str(ACE_REPO)
        from acestep.handler import AceStepHandler
        from acestep.inference import GenerationConfig, GenerationParams, generate_music
        from acestep.llm_inference import LLMHandler
        from acestep.model_downloader import ensure_lm_model, ensure_main_model

        ckpt = ACE_REPO / 'checkpoints'
        for ok, msg in [ensure_main_model(ckpt)] + ([] if a.no_lm else [ensure_lm_model('acestep-5Hz-lm-0.6B', ckpt)]):
            if not ok:
                sys.exit(msg)

        # Perfil 6-8 GB de la guía oficial: DiT 2B turbo + LM 0.6B (backend pt) con offload.
        dit = AceStepHandler()
        dit.initialize_service(
            project_root=str(ACE_REPO),
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

        config = GenerationConfig(batch_size=1, use_random_seed=True, audio_format='wav')
        for style, output in jobs:
            params = GenerationParams(
                caption=style['caption'],
                lyrics='[Instrumental]',
                instrumental=True,
                bpm=style['bpm'],
                keyscale=style['key'],
                timesignature=style['time_signature'],
                duration=a.duration,
                thinking=not a.no_lm,
            )
            r = generate_music(dit, llm, params, config, save_dir=str(output.parent))
            if not r.success:
                print(f'ACE-Step falló en {output.name}: {r.error}')
                continue
            Path(r.audios[0]['path']).replace(output)
            remaining = trim_silence(output)
            print(f'{output} ({remaining:.1f} s tras recortar el silencio; {style["key"]}, {style["bpm"]} BPM)')
