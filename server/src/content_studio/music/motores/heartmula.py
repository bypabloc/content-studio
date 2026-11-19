"""HeartMuLa 3B (Apache 2.0): solo recibe tags, sin tonalidad, BPM ni compás.

Corre en server/data/music/.venv-heartmula."""

from __future__ import annotations

import argparse
import importlib.util

from content_studio import rutas
from content_studio.music.evaluacion import recortar_silencio
from content_studio.music.motores.base import MotorMusica, Trabajos

HEART_CKPT = rutas.MUSIC / 'models' / 'heartmula-ckpt'


def descargar() -> None:
    from huggingface_hub import snapshot_download

    for repo, sub in [
        ('HeartMuLa/HeartMuLaGen', ''),
        ('HeartMuLa/HeartMuLa-oss-3B-happy-new-year', 'HeartMuLa-oss-3B'),
        ('HeartMuLa/HeartCodec-oss-20260123', 'HeartCodec-oss'),
    ]:
        snapshot_download(repo, local_dir=HEART_CKPT / sub)  # reanuda y salta lo ya bajado


class HeartMuLa(MotorMusica):
    def generar(self, trabajos: Trabajos, a: argparse.Namespace) -> None:
        import soundfile as sf
        import torch
        import torchaudio
        from heartlib import HeartMuLaGenPipeline

        # torchaudio 2.10 guarda vía torchcodec, que choca con el CUDA de este torch.
        torchaudio.save = lambda ruta, wav, sr: sf.write(ruta, wav.T.numpy(), sr)
        # heartlib usa torch.compile, que necesita triton (no existe en Windows) y falla recién al generar.
        if importlib.util.find_spec('triton') is None:
            torch._dynamo.config.disable = True
        descargar()
        # lazy_load: carga HeartMuLa, la descarga y recién ahí carga el codec (pico ~6 GB).
        pipe = HeartMuLaGenPipeline.from_pretrained(
            str(HEART_CKPT),
            device={'mula': torch.device('cuda'), 'codec': torch.device('cuda')},
            dtype={'mula': torch.bfloat16, 'codec': torch.float32},
            version='3B',
            lazy_load=True,
        )
        # Con un solo [Instrumental] corta a ~12 s; una sección cada ~20 s lo estira hasta el tope.
        secciones = ['[Intro]'] + ['[Instrumental]'] * max(1, int(a.duracion // 20)) + ['[Outro]']
        for estilo, salida in trabajos:
            with torch.no_grad():
                pipe(
                    {'lyrics': '\n\n'.join(secciones), 'tags': estilo['tags'] + ',instrumental'},
                    max_audio_length_ms=int(a.duracion * 1000),
                    save_path=str(salida),
                    topk=50,
                    temperature=1.0,
                    cfg_scale=1.5,
                )
            quedan = recortar_silencio(salida)
            print(f'{salida} ({quedan:.1f} s tras recortar el silencio)')
