"""TTS local con clonación de voz: Qwen3-TTS Base o Chatterbox Multilingual V3.

Uso (ver narration/README.md):
    python narration/tts.py --modelo qwen-0.6b --estilo amistosa \
        --texto "Hola, bienvenidos al canal."
    python narration/tts.py --modelo chatterbox --ref narration/voz/clara.wav \
        --estilo clara --archivo guion.txt --salida out/narration/guion.wav

--ref acepta un .wav o una carpeta con <estilo>.wav (por defecto narration/voz).
La transcripción va al lado con el mismo nombre y extensión .txt (Qwen la necesita).
Cada modelo corre en su propio venv (narration/.venv-qwen, narration/.venv-chatterbox).
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parent

# modelo: (venv, repo o versión, GiB de pesos). Medido en RTX 4060 8 GB, bf16.
MODELOS = {
    'qwen-1.7b': ('.venv-qwen', 'Qwen/Qwen3-TTS-12Hz-1.7B-Base', 3.95),
    'qwen-0.6b': ('.venv-qwen', 'Qwen/Qwen3-TTS-12Hz-0.6B-Base', 2.06),
    'chatterbox': ('.venv-chatterbox', 'v3', 0),
}
# VRAM de Qwen por encima de los pesos: ~1.15 GiB la primera frase de ~300
# letras y ~1.3 GiB cada frase extra del lote. Más de 4 no mejora en 8 GB.
GIB_PRIMERA, GIB_POR_FRASE, MARGEN_GIB = 1.15, 1.3, 0.5
LOTE_MAX = 4

# El estilo sale sobre todo de la referencia grabada en ese tono; estos valores
# solo lo empujan. velocidad se aplica con ffmpeg atempo (no cambia el tono).
ESTILOS = {
    'amistosa': dict(velocidad=1.05, temperature=0.8, exaggeration=0.6, cfg_weight=0.4),
    'suave': dict(velocidad=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'experta': dict(velocidad=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
    'clara': dict(velocidad=0.97, temperature=0.6, exaggeration=0.35, cfg_weight=0.6),
    'estable': dict(velocidad=1.05, temperature=0.6, exaggeration=0.3, cfg_weight=0.5),
}

MAX_CHARS = 300
PAUSA_SEG = 0.25


def usar_venv(venv: str) -> None:
    destino = AQUI / venv
    if Path(sys.prefix).resolve() == destino.resolve():
        return
    py = destino / 'bin' / 'python'
    if not py.exists():
        sys.exit(f'Falta {destino}. Ver "Instalación" en narration/README.md.')
    os.execv(py, [str(py), __file__, *sys.argv[1:]])


def resolver_ref(ref: Path, estilo: str) -> tuple[Path, str | None]:
    wav = ref / f'{estilo}.wav' if ref.is_dir() else ref
    if not wav.exists():
        sys.exit(f'No existe la referencia {wav}')
    txt = wav.with_suffix('.txt')
    return wav, txt.read_text(encoding='utf-8').strip() if txt.exists() else None


def lote_auto(libre_gib: float, pesos_gib: float) -> int:
    """Frases por pasada que caben en la VRAM libre.

    >>> lote_auto(7.9, 2.06), lote_auto(5.2, 2.06), lote_auto(7.9, 3.95), lote_auto(5.2, 3.95)
    (4, 2, 2, 1)
    """
    sobra = libre_gib - pesos_gib - GIB_PRIMERA - MARGEN_GIB
    return max(1, min(LOTE_MAX, 1 + int(sobra // GIB_POR_FRASE)))


def trozos(texto: str) -> list[str]:
    """Agrupa oraciones en bloques de hasta MAX_CHARS.

    >>> trozos('Hola. ' * 3)
    ['Hola. Hola. Hola.']
    >>> len(trozos('a' * 200 + '. ' + 'b' * 200 + '.'))
    2
    """
    out: list[str] = []
    for oracion in re.split(r'(?<=[.!?…])\s+', ' '.join(texto.split())):
        if out and len(out[-1]) + len(oracion) < MAX_CHARS:
            out[-1] += ' ' + oracion
        elif oracion:
            out.append(oracion)
    return out


def generar_qwen(repo, partes, wav_ref, texto_ref, p, lote):
    import torch
    from qwen_tts import Qwen3TTSModel

    model = Qwen3TTSModel.from_pretrained(repo, device_map='cuda:0', dtype=torch.bfloat16)
    prompt = model.create_voice_clone_prompt(
        ref_audio=str(wav_ref), ref_text=texto_ref, x_vector_only_mode=texto_ref is None,
    )
    audios = []
    for i in range(0, len(partes), lote):
        grupo = partes[i:i + lote]
        wavs, sr = model.generate_voice_clone(
            text=grupo, language=['Spanish'] * len(grupo), voice_clone_prompt=prompt * len(grupo),
            temperature=p['temperature'],
        )
        audios.extend(wavs)
    return audios, sr


def generar_chatterbox(version, partes, wav_ref, _texto_ref, p, _lote):
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    model = ChatterboxMultilingualTTS.from_pretrained(device='cuda', t3_model=version)
    audios = [
        model.generate(
            parte, language_id='es', audio_prompt_path=str(wav_ref),
            exaggeration=p['exaggeration'], cfg_weight=p['cfg_weight'],
            temperature=p['temperature'],
        ).squeeze(0).cpu().numpy()
        for parte in partes
    ]
    return audios, model.sr


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--modelo', choices=MODELOS, required=True)
    ap.add_argument('--ref', type=Path, default=AQUI / 'voz')
    ap.add_argument('--estilo', choices=ESTILOS, default='experta')
    fuente = ap.add_mutually_exclusive_group(required=True)
    fuente.add_argument('--texto')
    fuente.add_argument('--archivo', type=Path)
    ap.add_argument('--salida', type=Path, help='archivo .wav; por defecto out/narration/<modelo>-<estilo>.wav')
    ap.add_argument('--lote', type=int, help='frases por pasada en Qwen; por defecto según la VRAM libre')
    a = ap.parse_args()

    venv, repo, pesos = MODELOS[a.modelo]
    usar_venv(venv)

    import numpy as np
    import soundfile as sf
    import torch

    lote = a.lote or (1 if a.modelo == 'chatterbox' else lote_auto(torch.cuda.mem_get_info()[0] / 2**30, pesos))

    p = ESTILOS[a.estilo]
    wav_ref, texto_ref = resolver_ref(a.ref, a.estilo)
    texto = a.texto or a.archivo.read_text(encoding='utf-8')
    if texto_ref is None and a.modelo.startswith('qwen'):
        print(f'Aviso: falta {wav_ref.with_suffix(".txt")}; Qwen clona peor sin transcripción.')

    generar = generar_chatterbox if a.modelo == 'chatterbox' else generar_qwen
    t0 = time.perf_counter()
    audios, sr = generar(repo, trozos(texto), wav_ref, texto_ref, p, lote)
    total_s = time.perf_counter() - t0

    pausa = np.zeros(int(sr * PAUSA_SEG), dtype=np.float32)
    audio = np.concatenate([x for a_ in audios for x in (np.asarray(a_, dtype=np.float32), pausa)][:-1])

    salida = a.salida or ROOT / 'out' / 'narration' / f'{a.modelo}-{a.estilo}.wav'
    salida.parent.mkdir(parents=True, exist_ok=True)
    if p['velocidad'] == 1.0:
        sf.write(salida, audio, sr)
    else:
        crudo = salida.with_suffix('.crudo.wav')
        sf.write(crudo, audio, sr)
        subprocess.run(
            ['ffmpeg', '-y', '-loglevel', 'error', '-i', crudo, '-filter:a', f'atempo={p["velocidad"]}', salida],
            check=True,
        )
        crudo.unlink()
    dur = len(audio) / sr / p['velocidad']
    print(
        f'{salida} ({dur:.1f} s, {a.modelo}, {a.estilo}, lote {lote}) | '
        f'carga+generación {total_s:.1f} s, {dur / total_s:.2f}x tiempo real | '
        f'pico VRAM {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB'
    )


if __name__ == '__main__':
    main()
