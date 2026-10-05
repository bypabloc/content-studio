r"""TTS local con clonación de voz: Qwen3-TTS Base o Chatterbox Multilingual V3.

Uso (ver narration/README.md):
    python narration/tts.py --modelo qwen-0.6b --estilo amistosa \
        --texto "Hola, bienvenidos al canal."
    python narration/tts.py --modelo chatterbox --ref narration/voz/clara.wav \
        --estilo clara --archivo guion.txt --salida out/narration/guion.wav
    python narration/tts.py --modelo qwen-0.6b --archivo guiones/*.json --salida out/narration/lote

--ref acepta un .wav o una carpeta con <estilo>.wav (por defecto narration/voz).
La transcripción va al lado con el mismo nombre y extensión .txt (Qwen la necesita).
Cada modelo corre en su propio venv (narration/.venv-qwen, narration/.venv-chatterbox).

Pausas en el texto: una línea en blanco agrega 0.6 s; [pausa 1.5] agrega 1.5 s.
Otras marcas ([breath], <break>, **) se leen en voz alta. Ver narration/docs/formato-guion.md.
Un .json trae "texto" (lista de párrafos), "estilo" e "id" (nombre de la salida).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from functools import lru_cache
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
PAUSA_PARRAFO = 0.6
# Pausas que inserta el script: una línea en blanco o [pausa 1.5]. El modelo no las ve.
MARCA_PAUSA = re.compile(r'\[pausa\s+(\d+(?:[.,]\d+)?)\s*s?\]|\n[ \t]*\n', re.IGNORECASE)
# Qwen Base lee estas marcas en voz alta ("[breath]" sonó "Braids"). Ver docs/formato-guion.md.
ETIQUETA = re.compile(r'\[[^\]]*\]|<[^>]*>|\*\*|\(pausa\)', re.IGNORECASE)


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


def segmentos(texto: str) -> list[tuple[str, float]]:
    """Bloques a generar, cada uno con el silencio que va después.

    Una línea en blanco deja PAUSA_PARRAFO. [pausa N] deja N segundos: si
    hay alguna entre dos bloques, mandan esas marcas (se suman) y no las líneas en blanco.

    >>> segmentos('Hola. Chao.')
    [('Hola. Chao.', 0.0)]
    >>> segmentos('Uno.\\n\\nDos.')
    [('Uno.', 0.6), ('Dos.', 0.0)]
    >>> segmentos('Uno. [pausa 1,5] Dos. [PAUSA 2s]')
    [('Uno.', 1.5), ('Dos.', 2.0)]
    >>> segmentos('Uno.\\n\\n[pausa 0.2]\\n\\nDos.')
    [('Uno.', 0.2), ('Dos.', 0.0)]
    >>> segmentos('Uno.\\n \\n[pausa 1] [pausa 2]\\nDos.')
    [('Uno.', 3.0), ('Dos.', 0.0)]
    >>> [p for _, p in segmentos('a' * 200 + '. ' + 'b' * 200 + '.')]
    [0.25, 0.0]
    >>> segmentos('[pausa 1]\\n\\n')
    []
    """
    out: list[list] = []
    marcas, hay_marca, blanco, pos = 0.0, False, False, 0
    for m in [*MARCA_PAUSA.finditer(texto), None]:
        for t in trozos(texto[pos:m.start() if m else len(texto)]):
            if out:
                out[-1][1] = marcas if hay_marca else PAUSA_PARRAFO if blanco else PAUSA_SEG
            out.append([t, 0.0])
            marcas, hay_marca, blanco = 0.0, False, False
        if m:
            if m[1]:
                marcas, hay_marca = marcas + float(m[1].replace(',', '.')), True
            else:
                blanco = True
            pos = m.end()
    if out and hay_marca:
        out[-1][1] = marcas
    return [(t, p) for t, p in out]


def etiquetas(texto: str) -> list[str]:
    """Marcas que el modelo pronunciaría, sin contar las pausas propias.

    >>> etiquetas('Hola [breath] <break time="1s"/> **ojo** (pausa) [pausa 1]')
    ['[breath]', '<break time="1s"/>', '**', '(pausa)']
    >>> etiquetas('Texto limpio, con pausa.\\n\\nY otro párrafo.')
    []
    """
    return list(dict.fromkeys(ETIQUETA.findall(MARCA_PAUSA.sub(' ', texto))))


def recortar(audio, sr: int, umbral: float = 0.01, margen: float = 0.08):
    """Quita el silencio que el modelo deja en los bordes de cada bloque (~0.5 s por lado),
    para que las pausas insertadas duren lo indicado. Deja `margen` s para no cortar consonantes.

    >>> import numpy as np
    >>> x = np.r_[np.zeros(1000), np.full(500, 0.5), np.zeros(1000)].astype(np.float32)
    >>> len(recortar(x, 1000))
    660
    >>> len(recortar(np.zeros(100, dtype=np.float32), 1000))
    0
    """
    import numpy as np

    voz = np.flatnonzero(np.abs(audio) > umbral)
    if not voz.size:
        return audio[:0]
    m = int(sr * margen)
    return audio[max(0, voz[0] - m):voz[-1] + 1 + m]


def leer_json(d: dict) -> tuple[str, str | None]:
    """Texto y estilo de un guion JSON. Cada elemento de `texto` es un párrafo.

    >>> leer_json({'texto': ['Uno.', 'Dos.'], 'estilo': 'suave'})
    ('Uno.\\n\\nDos.', 'suave')
    >>> leer_json({'texto': 'Solo uno.'})
    ('Solo uno.', None)
    """
    t = d['texto']
    return '\n\n'.join(t) if isinstance(t, list) else t, d.get('estilo')


@lru_cache
def cargar_qwen(repo):
    import torch
    from qwen_tts import Qwen3TTSModel

    return Qwen3TTSModel.from_pretrained(repo, device_map='cuda:0', dtype=torch.bfloat16)


@lru_cache
def cargar_chatterbox(version):
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    return ChatterboxMultilingualTTS.from_pretrained(device='cuda', t3_model=version)


def generar_qwen(repo, partes, wav_ref, texto_ref, p, lote):
    model = cargar_qwen(repo)
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
    model = cargar_chatterbox(version)
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
    ap.add_argument('--estilo', choices=ESTILOS, help='por defecto el "estilo" del JSON, o experta')
    fuente = ap.add_mutually_exclusive_group(required=True)
    fuente.add_argument('--texto')
    fuente.add_argument('--archivo', type=Path, nargs='+', help='uno o varios .txt o .json; el modelo se carga una vez')
    ap.add_argument(
        '--salida', type=Path,
        help='con un solo guion, el .wav; con varios, la carpeta. Por defecto out/narration/',
    )
    ap.add_argument('--lote', type=int, help='frases por pasada en Qwen; por defecto según la VRAM libre')
    a = ap.parse_args()

    venv, repo, pesos = MODELOS[a.modelo]
    usar_venv(venv)

    import torch

    lote = a.lote or (1 if a.modelo == 'chatterbox' else lote_auto(torch.cuda.mem_get_info()[0] / 2**30, pesos))

    # (nombre de salida o None, texto, estilo del JSON o None)
    guiones = [(None, a.texto, None)] if a.texto else []
    for f in a.archivo or []:
        if f.suffix == '.json':
            d = json.loads(f.read_text(encoding='utf-8'))
            guiones.append((d.get('id', f.stem), *leer_json(d)))
        else:
            guiones.append((None, f.read_text(encoding='utf-8'), None))

    for nombre, texto, estilo_json in guiones:
        estilo = a.estilo or estilo_json or 'experta'
        if estilo not in ESTILOS:
            sys.exit(f'Estilo desconocido "{estilo}" en {nombre}. Opciones: {", ".join(ESTILOS)}')
        if len(guiones) == 1 and a.salida:
            salida = a.salida
        else:
            wav = f'{nombre}-{a.modelo}.wav' if nombre else f'{a.modelo}-{estilo}.wav'
            salida = (a.salida or ROOT / 'out' / 'narration') / wav
        narrar(a.modelo, repo, texto, estilo, a.ref, salida, lote)


def narrar(modelo, repo, texto, estilo, ref, salida, lote) -> None:
    import numpy as np
    import soundfile as sf
    import torch

    p = ESTILOS[estilo]
    wav_ref, texto_ref = resolver_ref(ref, estilo)
    if texto_ref is None and modelo.startswith('qwen'):
        print(f'Aviso: falta {wav_ref.with_suffix(".txt")}; Qwen clona peor sin transcripción.')

    if raras := etiquetas(texto):
        print(f'Aviso: el modelo va a leer en voz alta {", ".join(raras)}. Ver narration/docs/formato-guion.md.')
    segs = segmentos(texto)
    if not segs:
        sys.exit('El texto está vacío.')

    generar = generar_chatterbox if modelo == 'chatterbox' else generar_qwen
    t0 = time.perf_counter()
    audios, sr = generar(repo, [t for t, _ in segs], wav_ref, texto_ref, p, lote)
    total_s = time.perf_counter() - t0

    audio = np.concatenate([
        x for a_, (_, seg) in zip(audios, segs)
        for x in (recortar(np.asarray(a_, dtype=np.float32), sr), np.zeros(int(sr * seg), dtype=np.float32))
    ])

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
        f'{salida} ({dur:.1f} s, {modelo}, {estilo}, lote {lote}) | '
        f'generación {total_s:.1f} s, {dur / total_s:.2f}x tiempo real | '
        f'pico VRAM {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB'
    )


if __name__ == '__main__':
    main()
