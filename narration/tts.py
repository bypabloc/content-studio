r"""TTS local con clonación de voz: Qwen3-TTS, Chatterbox V3, OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3.

Uso (ver narration/README.md):
    python narration/tts.py --modelo qwen-0.6b --estilo amistosa \
        --texto "Hola, bienvenidos al canal."
    python narration/tts.py --modelo chatterbox --ref narration/voz/clara.wav \
        --estilo clara --archivo guion.txt --salida out/narration/guion.wav
    python narration/tts.py --modelo qwen-0.6b --archivo guiones/*.json --salida out/narration/lote
    python narration/tts.py --modelo omnivoice --archivo guion.txt --semilla 7 --evaluar

--ref acepta un .wav o una carpeta con <estilo>.wav (por defecto narration/voz). --voz usa una voz libre
del catálogo (narration/voces.py), solo si está aprobada en todos los estilos.
La transcripción va al lado con el mismo nombre y extensión .txt.
Cada motor corre en su propio venv (ver MOTORES). Cada toma deja un .json con sus metadatos.

Pausas en el texto: una línea en blanco agrega 0.6 s; [pausa 1.5] agrega 1.5 s.
Estilo y emoción por párrafo: [estilo: dramatica], [emocion: triste 0.4]. Gestos: [risa], [suspiro],
[respiro]; énfasis: [enfasis]palabra[/enfasis]. Cada motor recibe su traducción (ver TRADUCCION).
Otras marcas ([breath], <break>, **) se leen en voz alta. Ver narration/docs/formato-guion.md.
Un .json trae "texto" (lista de párrafos), "estilo" e "id" (nombre de la salida).
"""

import argparse
import gc
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parent
for _p in (str(AQUI), str(ROOT / 'src')):  # cli.py lo carga más de una vez
    if _p not in sys.path:
        sys.path.insert(0, _p)
from content_studio.comun import proceso  # noqa: E402  (solo stdlib)
# Ya migrado a src/content_studio/narration (paso 5 del refactor); se re-importa para voces.py, cli.py y los tests.
from content_studio.narration.audio import escribir, recortar  # noqa: E402
from content_studio.narration.estilos import EMOCIONES, ESTILOS, normalizar_vec  # noqa: E402
from content_studio.narration.evaluacion.revisar import (  # noqa: E402
    guardar_bloques, revisar, semilla_ronda, transcribir,
)
from content_studio.narration.guion import avisar_sobrescritura, planificar  # noqa: E402
from content_studio.narration.guion import guiones as leer_guiones  # noqa: E402
from content_studio.narration.texto.segmentos import etiquetas, segmentos  # noqa: E402
from content_studio.narration.texto.traducir import traducir  # noqa: E402
from voces import VOCES, aprobadas, mencion, catalogo as voces_catalogo  # noqa: E402  (stdlib: catálogo de voces)

# Un registro por --modelo. venv, repo y codigo son rutas relativas a narration/ o ids de Hugging Face.
# txt: 'obligatorio' (no clona sin la transcripción), 'opcional' (clona peor sin ella) o None (no la usa).
# Medido en RTX 4060 8 GB, bf16. Licencias en narration/README.md.
# Orden de preferencia (así salen en el menú del CLI): nota marca el ranking.
MOTORES = {
    'voxcpm2': dict(venv='.venv-voxcpm', repo='openbmb/VoxCPM2', licencia='Apache-2.0', comercial=True,
                    txt='opcional', ref_max_s=30, nota='★ recomendado'),
    'cosyvoice3': dict(venv='motores/CosyVoice/.venv', codigo='motores/CosyVoice',
                       repo='motores/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B',
                       licencia='Apache-2.0 (card: "academic purposes")', comercial=True, txt='obligatorio',
                       ref_max_s=30, nota='2.ª opción'),
    'qwen-1.7b': dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-1.7B-Base', pesos=3.95, lote=True,
                      licencia='Apache-2.0', comercial=True, txt='opcional', ref_max_s=60),
    'qwen-0.6b': dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-0.6B-Base', pesos=2.06, lote=True,
                      licencia='Apache-2.0', comercial=True, txt='opcional', ref_max_s=60),
    'chatterbox': dict(venv='.venv-chatterbox', repo='v3', licencia='MIT', comercial=True, txt=None,
                       ref_max_s=10),
    'omnivoice': dict(venv='.venv-omnivoice', repo='k2-fsa/OmniVoice', licencia='CC-BY-NC + Higgs Audio 2',
                      comercial=False, txt='obligatorio', ref_max_s=10),
    'indextts': dict(venv='motores/index-tts/.venv', codigo='motores/index-tts', repo='motores/index-tts/checkpoints',
                     licencia='bilibili Model Use License', comercial=False, txt=None, ref_max_s=15),
}
# Parámetros fijos de cada motor, los medidos en la investigación (docs/research/voicestudio-narracion/13).
PARAMS_MOTOR = {
    'omnivoice': dict(num_step=32, guidance_scale=2.0),
    'voxcpm2': dict(cfg_value=2.0, inference_timesteps=10, retry_badcase_max_times=1),
    'indextts': dict(max_text_tokens_per_segment=60),
}
# VRAM de Qwen por encima de los pesos: ~1.15 GiB la primera frase de ~300
# letras y ~1.3 GiB cada frase extra del lote. Más de 4 no mejora en 8 GB.
GIB_PRIMERA, GIB_POR_FRASE, MARGEN_GIB = 1.15, 1.3, 0.5
LOTE_MAX = 4

SYS_COSYVOICE = 'You are a helpful assistant.'  # prompt de sistema que CosyVoice 3 espera en zero-shot
IDIOMA_QWEN = {'es': 'Spanish', 'en': 'English'}


def usar_venv(venv: str, script: str = __file__) -> None:
    """Relanza `script` (por defecto este) con el python del venv, si no se está corriendo ya en él."""
    proceso.usar_venv(AQUI / venv, 'narration/README.md', script=script)


def avisos_voz(nombre: str, ficha: dict) -> None:
    """Lo que hay que saber antes de publicar una narración con una voz del catálogo: permiso del dueño y mención."""
    if not ficha.get('consentimiento'):
        print(f'Aviso: la voz {nombre} ({ficha["fuente"]}) tiene licencia {ficha["licencia"]}, pero su dueño no dio '
              'permiso para clonarla (regla 5 de AGENTS.md). Uso personal; para uso comercial, pídele permiso o usa una '
              'voz con consentimiento. Ver docs/research/voces-libres-clonacion/02.')
    if m := mencion(ficha):
        print(f'MENCIÓN OBLIGATORIA ({ficha["licencia"]}): pon este crédito en la descripción del video. Queda en el .json.')
        print(f'  {m}')
    if 'BY-SA' in ficha['licencia']:
        print('Aviso: licencia "compartir igual" (BY-SA). No pongas el clip original en el video, y si alguien considera '
              'la narración una adaptación, tendría que publicarse con la misma licencia. Ver '
              'docs/research/voces-libres-clonacion/12.')


def voz_de_referencia(ref: Path) -> dict | None:
    """Ficha del catálogo de la voz a la que pertenece una referencia (narration/voces/<voz>/<estilo>.wav), o None."""
    ref = Path(ref).resolve()
    if ref.parent.parent != VOCES.resolve():
        return None
    ficha = voces_catalogo().get(ref.parent.name)
    return ficha and {'voz': ref.parent.name, 'licencia': ficha['licencia'], 'fuente': ficha['fuente'],
                      'consentimiento': ficha.get('consentimiento', False), 'mencion': mencion(ficha)}


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


def lotes(indices: list[int], tam: int, clave) -> list[list[int]]:
    """Trozos de hasta `tam` índices consecutivos con la misma clave. Así Qwen agrupa por referencia.

    >>> lotes([0, 1, 2, 3, 4], 2, lambda i: i // 3)
    [[0, 1], [2], [3, 4]]
    >>> lotes([0, 1], 1, lambda i: 0)
    [[0], [1]]
    """
    out: list[list[int]] = []
    for i in indices:
        if out and len(out[-1]) < tam and clave(out[-1][0]) == clave(i):
            out[-1].append(i)
        else:
            out.append([i])
    return out


def fijar(semilla: int) -> None:
    """Fija las semillas de Python, numpy y torch. Se llama antes de cada bloque (o pasada de lote)."""
    import numpy as np
    import torch

    random.seed(semilla)
    np.random.seed(semilla)
    torch.manual_seed(semilla)
    torch.cuda.manual_seed_all(semilla)


# Cargadores: cada motor se carga una vez por proceso. liberar() los descarga antes de whisper.
@lru_cache
def cargar_qwen(repo):
    import torch
    from qwen_tts import Qwen3TTSModel

    return Qwen3TTSModel.from_pretrained(repo, device_map='cuda:0', dtype=torch.bfloat16)


@lru_cache
def cargar_chatterbox(version):
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    return ChatterboxMultilingualTTS.from_pretrained(device='cuda', t3_model=version)


@lru_cache
def cargar_omnivoice(repo):
    import torch
    from omnivoice import OmniVoice

    return OmniVoice.from_pretrained(repo, device_map='cuda', dtype=torch.float16)


@lru_cache
def cargar_voxcpm(repo):
    from voxcpm import VoxCPM

    return VoxCPM.from_pretrained(repo, load_denoiser=False, optimize=False)


@lru_cache
def cargar_indextts(codigo, ckpt):
    sys.path.insert(0, str(AQUI / codigo))
    # IndexTTS escribe checkpoints/hf_cache relativo al directorio actual: se fija antes de importarlo.
    os.environ['HF_HUB_CACHE'] = str(AQUI / ckpt / 'hf_cache')
    from indextts.infer_v2_5 import IndexTTS2

    return IndexTTS2(cfg_path=str(AQUI / ckpt / 'config.yaml'), model_dir=str(AQUI / ckpt), use_bf16=True,
                     use_cuda_kernel=False, use_deepspeed=False, use_qwen_emo=False)


@lru_cache
def cargar_cosyvoice(codigo, ckpt):
    import soundfile as sf
    import torch
    import torchaudio

    sys.path[:0] = [str(AQUI / codigo), str(AQUI / codigo / 'third_party' / 'Matcha-TTS')]

    def leer_wav(path, *_a, **_k):  # torchaudio 2.11 exige torchcodec; soundfile alcanza para WAV
        data, sr = sf.read(str(path), dtype='float32', always_2d=True)
        return torch.from_numpy(data.T.copy()), sr

    torchaudio.load = leer_wav
    from cosyvoice.cli.cosyvoice import AutoModel

    return AutoModel(model_dir=str(AQUI / ckpt))


@lru_cache
def prompt_qwen(modelo, ref, texto_ref):
    return modelo.create_voice_clone_prompt(ref_audio=ref, ref_text=texto_ref, x_vector_only_mode=texto_ref is None)


@lru_cache
def prompt_omnivoice(modelo, ref, texto_ref):
    return modelo.create_voice_clone_prompt(ref_audio=ref, ref_text=texto_ref)


CARGADORES = (cargar_qwen, cargar_chatterbox, cargar_omnivoice, cargar_voxcpm, cargar_indextts, cargar_cosyvoice)
PROMPTS = (prompt_qwen, prompt_omnivoice)


def liberar() -> None:
    """Descarga los modelos y sus prompts de la VRAM (antes de whisper y al regenerar)."""
    import torch

    for f in (*CARGADORES, *PROMPTS):
        f.cache_clear()
    gc.collect()
    torch.cuda.empty_cache()


# Un generador por motor, con la misma firma: (registro, bloques, idioma) -> (audios, sr).
# Cada bloque trae lo que recibe el motor (ver preparar_bloques): 'enviar', 'ref', 'texto_ref', 'p' y 'emo'.
def generar_qwen(m, bloques, idioma):
    modelo = cargar_qwen(m['repo'])
    b = bloques[0]  # lotes() agrupa bloques con la misma referencia y temperatura
    prompt = prompt_qwen(modelo, str(b['ref']), b['texto_ref'])
    return modelo.generate_voice_clone(
        text=[x['enviar'] for x in bloques], language=[IDIOMA_QWEN[idioma]] * len(bloques),
        voice_clone_prompt=prompt * len(bloques), temperature=b['p']['temperature'],
    )


def generar_chatterbox(m, bloques, idioma):
    modelo = cargar_chatterbox(m['repo'])
    audios = [
        modelo.generate(
            b['enviar'], language_id=idioma, audio_prompt_path=str(b['ref']),
            exaggeration=b['p']['exaggeration'], cfg_weight=b['p']['cfg_weight'], temperature=b['p']['temperature'],
        ).squeeze(0).cpu().numpy()
        for b in bloques
    ]
    return audios, modelo.sr


def generar_omnivoice(m, bloques, idioma):
    modelo = cargar_omnivoice(m['repo'])
    audios = []
    for b in bloques:
        prompt = prompt_omnivoice(modelo, str(b['ref']), b['texto_ref'])
        audios.append(
            modelo.generate(text=b['enviar'], language=idioma, voice_clone_prompt=prompt,
                            **PARAMS_MOTOR['omnivoice'])[0],
        )
    return audios, modelo.sampling_rate


def generar_voxcpm(m, bloques, idioma):
    modelo = cargar_voxcpm(m['repo'])
    audios = []
    for b in bloques:
        kw = dict(reference_wav_path=str(b['ref']), max_len=min(4096, max(256, len(b['enviar']) * 6)),
                  **PARAMS_MOTOR['voxcpm2'])
        if b['texto_ref']:  # Hi-Fi. Con emoción (controlable) no va la transcripción: se leería la instrucción
            kw.update(prompt_wav_path=str(b['ref']), prompt_text=b['texto_ref'])
        audios.append(modelo.generate(text=b['enviar'], **kw))
    return audios, modelo.tts_model.sample_rate


def generar_indextts(m, bloques, idioma):
    import soundfile as sf

    modelo = cargar_indextts(m['codigo'], m['repo'])
    audios = []
    for b in bloques:
        kw = dict(PARAMS_MOTOR['indextts'])
        if b['emo']:
            kw['emo_alpha'] = b['emo']['alpha']
            if 'clip' in b['emo']:
                kw['emo_audio_prompt'] = str(b['emo']['clip'])
            else:
                kw['emo_vector'] = b['emo']['vector']
        fd, tmp = tempfile.mkstemp(suffix='.wav', dir='/dev/shm' if os.path.isdir('/dev/shm') else None)
        os.close(fd)
        try:
            modelo.infer(spk_audio_prompt=str(b['ref']), text=b['enviar'], lang=idioma, output_path=tmp,
                         verbose=False, **kw)
            audio, sr = sf.read(tmp, dtype='float32')
        finally:
            os.unlink(tmp)
        audios.append(audio if audio.ndim == 1 else audio.mean(axis=1))
    return audios, sr


def generar_cosyvoice(m, bloques, idioma):
    import torch

    modelo = cargar_cosyvoice(m['codigo'], m['repo'])
    audios = []
    for b in bloques:
        if b['emo']:  # instruct2: la instrucción reemplaza a la transcripción de la referencia
            partes = modelo.inference_instruct2(
                b['enviar'], f"{SYS_COSYVOICE} {b['emo']['instruccion']}<|endofprompt|>", str(b['ref']),
                stream=False, text_frontend=False,
            )
        else:
            partes = modelo.inference_zero_shot(
                b['enviar'], f'{SYS_COSYVOICE}<|endofprompt|>{b["texto_ref"]}', str(b['ref']),
                stream=False, text_frontend=False,
            )
        audios.append(torch.cat([j['tts_speech'] for j in partes], dim=1).squeeze(0).cpu().numpy())
    return audios, modelo.sample_rate


GENERADORES = {
    'qwen-1.7b': generar_qwen, 'qwen-0.6b': generar_qwen, 'chatterbox': generar_chatterbox,
    'omnivoice': generar_omnivoice, 'voxcpm2': generar_voxcpm, 'indextts': generar_indextts,
    'cosyvoice3': generar_cosyvoice,
}


def construir_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para preguntar los que faltan y mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--modelo', choices=MOTORES, default='voxcpm2',
                    help='motor TTS (por defecto voxcpm2; ver narration/README.md)')
    ap.add_argument('--ref', type=Path, default=AQUI / 'voz', help='carpeta de referencias o un .wav concreto')
    ap.add_argument('--voz', choices=list(aprobadas(ESTILOS)),
                    help='voz libre del catálogo, aprobada en todos los estilos (narration/voces.py); reemplaza --ref')
    ap.add_argument('--estilo', choices=ESTILOS, help='por defecto el "estilo" del JSON, o experta')
    fuente = ap.add_mutually_exclusive_group(required=True)
    fuente.add_argument('--texto', help='texto a narrar, entre comillas')
    fuente.add_argument('--archivo', type=Path, nargs='+', help='uno o varios .txt o .json; el modelo se carga una vez')
    ap.add_argument(
        '--salida', type=Path,
        help='con un solo guion, el .wav; con varios, la carpeta. Por defecto out/narration/',
    )
    ap.add_argument('--lote', type=int, help='frases por pasada en Qwen; por defecto según la VRAM libre')
    ap.add_argument('--semilla', type=int, help='semilla base; por defecto aleatoria. Se imprime y queda en el .json')
    ap.add_argument(
        '--master', choices=['voz', 'no'], default='voz',
        help='voz: loudness de --lufs con pasa-altos de 70 Hz, sin compresión salvo que el pico lo impida; no: sin procesar',
    )
    ap.add_argument('--lufs', type=float, default=-16.0, help='loudness objetivo de --master voz (por defecto -16)')
    ap.add_argument(
        '--idioma', choices=['es', 'en'], default='es',
        help='idioma del motor y de whisper; con en, el estilo por defecto es neutral-en',
    )
    ap.add_argument(
        '--evaluar', action='store_true',
        help='al final transcribe cada salida con whisper y la compara, párrafo por párrafo, con el texto pedido',
    )
    ap.add_argument(
        '--reintentos', type=int, default=0,
        help='con --evaluar: rondas en las que se regeneran solo los párrafos con observaciones',
    )
    return ap


def main() -> None:
    ap = construir_parser()
    a = ap.parse_args()
    if a.reintentos and not a.evaluar:
        ap.error('--reintentos necesita --evaluar')
    if a.voz:
        ficha = aprobadas(ESTILOS)[a.voz]
        if ficha['idioma'] != a.idioma:
            ap.error(f'la voz {a.voz} es en "{ficha["idioma"]}": usa --idioma {ficha["idioma"]}')
        a.ref = VOCES / a.voz

    guiones = leer_guiones(a)
    trabajos = planificar(a, guiones)  # valida estilos y rutas antes de relanzar y de cargar el modelo

    m = MOTORES[a.modelo]
    usar_venv(m['venv'])  # desde aquí corre en el venv del motor: los avisos se imprimen una sola vez
    if a.voz:
        avisos_voz(a.voz, aprobadas(ESTILOS)[a.voz])
    avisar_sobrescritura(trabajos)

    import torch

    lote = a.lote or (lote_auto(torch.cuda.mem_get_info()[0] / 2**30, m['pesos']) if m.get('lote') else 1)
    semilla = a.semilla if a.semilla is not None else random.randrange(2**31)
    print(f'Semilla: {semilla}')
    if not m['comercial']:
        print(f'Aviso: {a.modelo} tiene licencia no comercial ({m["licencia"]}). Solo uso personal.')
    elif 'academic' in m['licencia']:
        print(f'Aviso: {a.modelo} es Apache-2.0, pero su model card dice "for academic purposes only" (sin aclarar). '
              'Ver docs/research/voicestudio-narracion/07.')

    resultados = [narrar(a.modelo, texto, estilo, a.ref, salida, lote, semilla, idioma=a.idioma, master=a.master,
                         lufs=a.lufs) for texto, estilo, salida in trabajos]

    if a.evaluar:
        evaluar(a.modelo, resultados, lote, semilla, a.reintentos, a.idioma)
    elif a.modelo == 'omnivoice':
        print('Sugerencia: usa --evaluar con omnivoice')
    for g in resultados:
        guardar_metadatos(a.modelo, g)


def evaluar(modelo: str, resultados: list[dict], lote: int, semilla: int, reintentos: int, idioma: str) -> None:
    if not shutil.which('whisper'):
        sys.exit('Falta el comando whisper (pip install openai-whisper); no se puede evaluar.')
    informe: dict[int, tuple[list[str], list[int]]] = {}  # guion -> (observaciones, bloques con error)
    pendientes = {k: list(range(len(g['segs']))) for k, g in enumerate(resultados)}  # guion -> bloques
    for ronda in range(reintentos + 1):
        liberar()  # libera la VRAM para whisper
        transcribir([w for k, idx in pendientes.items() for w in guardar_bloques(resultados[k], idx)], idioma)
        for k in pendientes:
            informe[k] = revisar(resultados[k])
        pendientes = {k: informe[k][1] for k in pendientes if informe[k][1]}
        if not pendientes or ronda == reintentos:
            break
        n = sum(map(len, pendientes.values()))
        print(f'Reintento {ronda + 1}/{reintentos}: regenerando {n} párrafo(s) de {len(pendientes)} guion(es)...')
        for k, idx in pendientes.items():
            regenerar(modelo, resultados[k], idx, lote, semilla_ronda(semilla, ronda + 1))

    for k, g in enumerate(resultados):
        problemas, fallidos = informe[k]
        g['evaluacion'] = {'rondas': ronda + 1, 'observaciones': problemas, 'ok': not fallidos}
        print(f'{"REVISAR" if fallidos else "OK     "} {g["salida"]}')
        for linea in problemas:
            print(f'          {linea}')
    revisar_n = sum(bool(f) for _, f in informe.values())
    print(f'{len(resultados) - revisar_n}/{len(resultados)} sin errores (los avisos de ritmo no cuentan).')


def preparar_bloques(motor: str, segs: list[dict], ref: Path) -> list[dict]:
    """Lo que recibe el motor en cada bloque (§6): referencia, texto traducido, parámetros y control de emoción.
    Un bloque que queda vacío tras traducir no se puede generar: se corta antes de empezar."""
    import soundfile as sf

    m = MOTORES[motor]
    refs: dict[str, tuple[Path, str | None]] = {}
    carpeta_voz = ref if ref.is_dir() else ref.parent

    def de_estilo(nombre: str) -> tuple[Path, str | None]:
        if nombre not in refs:
            wav, txt = resolver_ref(ref, nombre)
            dur = sf.info(str(wav)).duration
            if dur > m['ref_max_s']:
                print(f'Aviso: {wav.name} dura {dur:.1f} s; para {motor} conviene hasta {m["ref_max_s"]} s.')
            if txt is None and m['txt'] == 'obligatorio':
                sys.exit(f'Falta {wav.with_suffix(".txt")}: {motor} necesita la transcripción de la referencia.')
            if txt is None and m['txt'] == 'opcional':
                print(f'Aviso: falta {wav.with_suffix(".txt")}; {motor} clona peor sin transcripción.')
            refs[nombre] = (wav, txt)
        return refs[nombre]

    pbs = []
    for i, b in enumerate(segs):
        envio, av = traducir(b['texto'], motor)
        avisos = b['avisos'] + av
        if not envio:
            sys.exit(f'El párrafo {i + 1} queda vacío para {motor}: revisa sus marcas.')
        wav, txt = de_estilo(b['estilo'])
        p = dict(ESTILOS[b['estilo']])
        modo = {'voxcpm2': 'hifi', 'cosyvoice3': 'zero_shot'}.get(motor, 'clonacion')
        if modo == 'hifi' and not txt:
            modo = 'clonacion'
        emo, emocion = None, None
        if b['emocion']:
            nombre, inten = b['emocion']
            E = EMOCIONES[nombre]
            marca = {'nombre': nombre, 'intensidad': inten}
            if motor == 'omnivoice' or motor.startswith('qwen'):
                if E['ref'] and ref.is_dir() and (ref / f'{E["ref"]}.wav').exists():
                    wav, txt = de_estilo(E['ref'])
                    modo, emocion = 'referencia', marca
                else:
                    avisos.append(f'no hay referencia para "{nombre}"; se genera con el estilo {b["estilo"]}')
            elif motor == 'chatterbox':
                if E['chatterbox']:
                    k = inten / 0.6  # la tabla está medida a intensidad 0.6: a esa, los valores son los de la tabla
                    ex, cfg = E['chatterbox']
                    ex, cfg = round(0.5 + (ex - 0.5) * k, 3), round(0.5 + (cfg - 0.5) * k, 3)
                    p.update(exaggeration=ex, cfg_weight=cfg)
                    modo, emocion = 'parametros', {**marca, 'exaggeration': ex, 'cfg_weight': cfg}
                else:
                    avisos.append(f'chatterbox no tiene valores para "{nombre}"; usa [estilo: intima]')
            elif motor == 'indextts':
                clip = carpeta_voz / 'emociones' / f'{nombre}.wav'
                if clip.exists():
                    emo, modo, emocion = {'clip': clip, 'alpha': inten}, 'clip', marca
                elif E['vector']:
                    vec = [0.0] * 8
                    for j, val in E['vector'].items():
                        vec[j] = val
                    emo, modo, emocion = {'vector': normalizar_vec(vec), 'alpha': inten}, 'vector', marca
                else:
                    avisos.append(f'IndexTTS no tiene vector para "{nombre}"; usa [estilo: intima]')
            elif motor == 'voxcpm2':
                envio = f'({E["voxcpm"]}){envio}'  # la instrucción va en el texto; con Hi-Fi se leería
                txt, modo, emocion = None, 'controlable', marca
            elif motor == 'cosyvoice3':
                if E['cosy']:
                    emo, modo, emocion = {'instruccion': E['cosy']}, 'instruct2', marca
                else:
                    avisos.append(f'cosyvoice3 no sigue "{nombre}"; se genera sin emoción')
            if emocion and inten != 0.6 and motor in ('voxcpm2', 'cosyvoice3'):
                avisos.append(f'{motor} no controla la intensidad de la emoción; se ignora')
        pbs.append(dict(
            texto=b['texto'], estilo=b['estilo'], enviar=envio, ref=wav, texto_ref=txt, p=p, emo=emo,
            emocion=emocion, modo=modo, avisos=avisos,
        ))
    return pbs


def narrar(modelo, texto, estilo, ref, salida, lote, semilla, idioma='es', master='voz', lufs=-16.0) -> dict:
    """Genera todos los bloques del texto y escribe el .wav. Devuelve lo necesario para evaluar,
    regenerar bloques sueltos y escribir los metadatos."""
    import torch

    segs = segmentos(texto, estilo)
    if not segs:
        sys.exit('El texto está vacío.')
    for i, b in enumerate(segs):
        if b['estilo'] not in ESTILOS:
            sys.exit(f'Estilo desconocido "{b["estilo"]}" en el párrafo {i + 1}. Opciones: {", ".join(ESTILOS)}')
        if b['emocion'] and b['emocion'][0] not in EMOCIONES:
            sys.exit(f'Emoción desconocida "{b["emocion"][0]}" en el párrafo {i + 1}. Opciones: {", ".join(EMOCIONES)}')
        if b['emocion'] and not 0 <= b['emocion'][1] <= 1:
            sys.exit(f'La intensidad de la emoción en el párrafo {i + 1} tiene que estar entre 0 y 1.')
    if raras := etiquetas(texto):
        print(f'Aviso: el modelo va a leer en voz alta {", ".join(raras)}. Ver narration/docs/formato-guion.md.')
    pb = preparar_bloques(modelo, segs, ref)
    for i, p_ in enumerate(pb):
        for a in p_['avisos']:
            print(f'Aviso: párrafo {i + 1}: {a}')

    g = dict(
        salida=salida, segs=segs, pb=pb, estilo=estilo, p=ESTILOS[estilo], idioma=idioma, semilla=semilla,
        semillas=[], semilla_bloque=[None] * len(segs), audios=[], sr=0, bloques=[], tiempo_s=0.0,
        master=master, lufs=lufs, master_info=None,
    )
    regenerar(modelo, g, range(len(segs)), lote, semilla)
    dur = g['bloques'][-1][2]
    print(
        f'{salida} ({dur:.1f} s, {modelo}, {estilo}, lote {lote}) | '
        f'generación {g["tiempo_s"]:.1f} s, {dur / g["tiempo_s"]:.2f}x tiempo real | '
        f'pico VRAM {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB',
        flush=True,
    )
    return g


def regenerar(modelo: str, g: dict, indices, lote: int, semilla: int) -> None:
    """(Re)genera los bloques indicados del guion `g` con la semilla de la ronda y reescribe su .wav.
    Qwen genera hasta `lote` bloques de la misma referencia por pasada; el resto de a uno."""
    import numpy as np

    m = MOTORES[modelo]
    tam = lote if m.get('lote') else 1
    if not g['audios']:
        g['audios'] = [None] * len(g['segs'])
    g['semillas'].append(semilla)
    t0 = time.perf_counter()
    for grupo in lotes(list(indices), tam, lambda i: (g['pb'][i]['ref'], g['pb'][i]['p']['temperature'])):
        fijar(semilla)  # la semilla se fija antes de cada bloque o pasada (§4)
        audios, g['sr'] = GENERADORES[modelo](m, [g['pb'][i] for i in grupo], g['idioma'])
        for i, a_ in zip(grupo, audios):
            g['audios'][i] = recortar(np.asarray(a_, dtype=np.float32), g['sr'])
            g['semilla_bloque'][i] = semilla
            aviso = 'el motor no produjo voz; si el párrafo termina sin . ? ! (corte a mitad de oración), puntúalo'
            if not len(g['audios'][i]) and aviso not in g['pb'][i]['avisos']:
                print(f'Aviso: párrafo {i + 1}: {aviso}')
                g['pb'][i]['avisos'].append(aviso)
    g['tiempo_s'] += time.perf_counter() - t0
    escribir(g)


def guardar_metadatos(modelo: str, g: dict) -> None:
    """Escribe <salida>.json con lo necesario para reproducir la toma: motor, semillas, referencias y bloques."""
    import torch

    m = MOTORES[modelo]
    hashes: dict[Path, str] = {}
    bloques = []
    for i, (b, pb, (_, ini, fin)) in enumerate(zip(g['segs'], g['pb'], g['bloques'])):
        if pb['ref'] not in hashes:
            hashes[pb['ref']] = sha256(pb['ref'])
        bloques.append({
            'i': i + 1, 'texto_guion': b['texto'], 'texto_enviado': pb['enviar'], 'estilo': pb['estilo'],
            'referencia': str(pb['ref']), 'referencia_sha256': hashes[pb['ref']],
            'emocion': pb['emocion'], 'modo': pb['modo'], 'pausa_despues': b['pausa'],
            'inicio_s': round(ini, 3), 'fin_s': round(fin, 3), 'semilla': g['semilla_bloque'][i],
            'avisos': pb['avisos'],
        })
    meta = {
        'version_tts': version_tts(), 'fecha': datetime.now().astimezone().isoformat(timespec='seconds'),
        'motor': modelo, 'licencia': m['licencia'], 'comercial': m['comercial'], 'idioma': g['idioma'],
        'semilla': g['semilla'], 'semillas_por_ronda': g['semillas'], 'bloques': bloques,
        'master': g['master_info'], 'evaluacion': g.get('evaluacion'),
        'parametros': {**g['p'], **PARAMS_MOTOR.get(modelo, {})},
        'tiempo_generacion_s': round(g['tiempo_s'], 1), 'duracion_s': round(g['bloques'][-1][2], 2),
        'vram_pico_gib': round(torch.cuda.max_memory_reserved() / 2**30, 2),
        # Voces del catálogo usadas en la toma, con la mención que pide su licencia (para la descripción del video).
        'voces': list({v['voz']: v for pb in g['pb'] if (v := voz_de_referencia(pb['ref']))}.values()) or None,
    }
    g['salida'].with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')


def sha256(ruta) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def version_tts() -> str:
    """Commit del script; con '-dirty' si hay cambios sin confirmar (la toma no sería reproducible con ese commit)."""
    r = subprocess.run(['git', 'describe', '--always', '--dirty', '--abbrev=7'], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() or 'desconocida'


if __name__ == '__main__':
    main()
