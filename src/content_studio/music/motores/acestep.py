"""ACE-Step 1.5 (MIT): DiT 2B turbo + planificador LM 0.6B, con offload para 8 GB. Corre en music/.venv-acestep."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from content_studio import rutas
from content_studio.music.evaluacion import recortar_silencio
from content_studio.music.motores.base import MotorMusica

ACE_REPO = rutas.MUSIC / 'models' / 'ACE-Step-1.5'


class AceStep(MotorMusica):
    def generar(self, trabajos, a) -> None:
        os.environ['ACESTEP_PROJECT_ROOT'] = str(ACE_REPO)
        from acestep.handler import AceStepHandler
        from acestep.inference import GenerationConfig, GenerationParams, generate_music
        from acestep.llm_inference import LLMHandler
        from acestep.model_downloader import ensure_lm_model, ensure_main_model

        ckpt = ACE_REPO / 'checkpoints'
        for ok, msg in [ensure_main_model(ckpt)] + ([] if a.sin_lm else [ensure_lm_model('acestep-5Hz-lm-0.6B', ckpt)]):
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
        if not a.sin_lm:
            llm.initialize(
                checkpoint_dir=str(ckpt),
                lm_model_path='acestep-5Hz-lm-0.6B',
                backend='pt',
                device='cuda',
                offload_to_cpu=True,
            )

        config = GenerationConfig(batch_size=1, use_random_seed=True, audio_format='wav')
        for estilo, salida in trabajos:
            params = GenerationParams(
                caption=estilo['caption'],
                lyrics='[Instrumental]',
                instrumental=True,
                bpm=estilo['bpm'],
                keyscale=estilo['tono'],
                timesignature=estilo['compas'],
                duration=a.duracion,
                thinking=not a.sin_lm,
            )
            r = generate_music(dit, llm, params, config, save_dir=str(salida.parent))
            if not r.success:
                print(f'ACE-Step falló en {salida.name}: {r.error}')
                continue
            Path(r.audios[0]['path']).replace(salida)
            quedan = recortar_silencio(salida)
            print(f'{salida} ({quedan:.1f} s tras recortar el silencio; {estilo["tono"]}, {estilo["bpm"]} BPM)')
