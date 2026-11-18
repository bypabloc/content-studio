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
import difflib
import gc
import hashlib
import json
import os
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime
from functools import lru_cache
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parent
sys.path.insert(0, str(AQUI))
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

# El estilo sale sobre todo de la referencia grabada en ese tono; estos valores
# solo lo empujan. velocidad se aplica con ffmpeg atempo (no cambia el tono).
ESTILOS = {
    'amistosa': dict(velocidad=1.05, temperature=0.8, exaggeration=0.6, cfg_weight=0.4),
    'suave': dict(velocidad=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'experta': dict(velocidad=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
    'clara': dict(velocidad=0.97, temperature=0.6, exaggeration=0.35, cfg_weight=0.6),
    'estable': dict(velocidad=1.05, temperature=0.6, exaggeration=0.3, cfg_weight=0.5),
    'neutral': dict(velocidad=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
    'energica': dict(velocidad=1.0, temperature=0.8, exaggeration=0.7, cfg_weight=0.3),
    'dramatica': dict(velocidad=1.0, temperature=0.7, exaggeration=0.6, cfg_weight=0.3),
    'triste': dict(velocidad=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'intima': dict(velocidad=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'susurro': dict(velocidad=1.0, temperature=0.7, exaggeration=0.3, cfg_weight=0.5),
    'neutral-en': dict(velocidad=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
}

MAX_CHARS = 300
PAUSA_SEG = 0.25
PAUSA_PARRAFO = 0.6
# Marcas que cortan el texto en bloques: [pausa N] (grupo 1), [estilo: nombre] (2),
# [emocion: nombre 0.4] (3 y 4) y la línea en blanco. El modelo no las ve.
MARCA_BLOQUE = re.compile(
    r'\[pausa\s+(\d+(?:[.,]\d+)?)\s*s?\]'
    r'|\[estilo:\s*([\w-]*)\s*\]'
    r'|\[emocion:\s*(\w*)\s*(\d+(?:[.,]\d+)?)?\s*\]'
    r'|\n[ \t]*\n',
    re.IGNORECASE,
)
# Todas las marcas de la gramática, para quitarlas antes de comparar o de buscar etiquetas ajenas.
SIN_MARCAS = re.compile(
    r'\[pausa\s+[\d.,]+\s*s?\]|\[estilo:[^\]]*\]|\[emocion:[^\]]*\]'
    r'|\[(?:risa|suspiro|respiro)\]|\[/?enfasis\]|\n[ \t]*\n',
    re.IGNORECASE,
)
# Gestos y énfasis: van dentro del texto del bloque y traducir() los convierte según el motor (§6.3).
GESTO = re.compile(r'\[(risa|suspiro|respiro)\]', re.IGNORECASE)
ENFASIS = re.compile(r'\[enfasis\](.*?)\[/enfasis\]', re.IGNORECASE | re.DOTALL)
SUSPENSIVOS = re.compile(r'…(?=\s+\w)')  # "…" a mitad de oración: lo que sigue sigue la misma oración
# Qwen Base lee estas marcas en voz alta ("[breath]" sonó "Braids"). Ver docs/formato-guion.md.
ETIQUETA = re.compile(r'\[[^\]]*\]|<[^>]*>|\*\*|\(pausa\)', re.IGNORECASE)

# --evaluar: whisper transcribe la salida y se compara con el texto pedido.
WHISPER_MODELO = 'medium'  # small confundía palabras ("horarios" -> "cerrarios")
SILENCIO_MAX = 1.3  # criterio: un silencio más largo dentro de un párrafo es una pausa que nadie pidió
RITMO_TOLERANCIA = (0.7, 1.4)  # criterio: palabras/s del párrafo frente a la mediana del guion
# Nombre de cada letra (sin tildes) -> letra, para que "pe de efe" y "PDF" se comparen igual.
LETRA = {
    'a': 'a', 'be': 'b', 'ce': 'c', 'de': 'd', 'e': 'e', 'efe': 'f', 'ge': 'g', 'hache': 'h', 'i': 'i',
    'jota': 'j', 'ka': 'k', 'ele': 'l', 'eme': 'm', 'ene': 'n', 'o': 'o', 'pe': 'p', 'cu': 'q', 'erre': 'r',
    'ese': 's', 'te': 't', 'u': 'u', 've': 'v', 'uve': 'v', 'equis': 'x', 'ye': 'y', 'zeta': 'z',
}
# Nombres de letra que no son palabras comunes: si una racha incluye uno, es una sigla.
LETRA_CLARA = set(LETRA) - {'a', 'de', 'e', 'i', 'o', 'u', 'ye', 'te', 'ese', 've'}
# En inglés los números no se comparan: whisper escribe "7", "seven" o "$7" según le parezca, y no hay normalizador
# de números en inglés. Se quitan de los dos lados, junto con "and" ("one hundred and five") y con las unidades de
# moneda y porcentaje que whisper cambia por símbolo ("$7.20", "5%").
# ponytail: sin num2words; comparar números exigiría convertirlos a dígitos en los dos lados.
NUMEROS_EN = {
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
    'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty', 'forty',
    'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred', 'thousand', 'million', 'and',
    'dollar', 'dollars', 'cent', 'cents', 'percent',
}
SYS_COSYVOICE = 'You are a helpful assistant.'  # prompt de sistema que CosyVoice 3 espera en zero-shot
IDIOMA_QWEN = {'es': 'Spanish', 'en': 'English'}

# Emociones (§6.1). vector: índices de IndexTTS [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm].
# voxcpm y cosy: instrucción de VoxCPM2 y de CosyVoice 3. chatterbox: (exaggeration, cfg_weight) a intensidad 0.6.
# ref: estilo de referencia que la representa en Qwen y OmniVoice (None: no hay).
EMOCIONES = {
    'alegre': dict(vector={0: 0.8}, voxcpm='cheerful and energetic',
                   cosy='Please speak in a cheerful and energetic tone.', chatterbox=(0.7, 0.3), ref='energica'),
    'triste': dict(vector={2: 0.8}, voxcpm='sad and slow', cosy='Please speak in a sad and slow tone.',
                   chatterbox=(0.4, 0.5), ref='triste'),
    'enojado': dict(vector={1: 0.8}, voxcpm='angry and firm', cosy='Please speak in an angry tone.',
                    chatterbox=(0.8, 0.3), ref=None),
    'miedo': dict(vector={3: 0.8}, voxcpm='tense and fearful', cosy='Please speak in a fearful tone.',
                  chatterbox=(0.6, 0.3), ref='dramatica'),
    'sorpresa': dict(vector={6: 0.8}, voxcpm='surprised and amazed', cosy='Please speak in a surprised tone.',
                     chatterbox=(0.7, 0.3), ref='amistosa'),
    'calma': dict(vector={7: 0.8}, voxcpm='calm and confident', cosy='Please speak in a calm, warm tone.',
                  chatterbox=(0.3, 0.5), ref='suave'),
    'urgente': dict(vector={3: 0.5, 6: 0.3}, voxcpm='urgent, speaking fast',
                    cosy='Please speak in an urgent tone, speaking fast.', chatterbox=(0.7, 0.3), ref='energica'),
    'susurro': dict(vector=None, voxcpm='whispering', cosy=None, chatterbox=None, ref='intima'),
}
# Sesgo del vector de emoción de la WebUI de IndexTTS (§6.2).
SESGO_INDEXTTS = [0.9375, 0.875, 1.0, 1.0, 0.9375, 0.9375, 0.6875, 0.5625]
# Cómo traduce cada motor las marcas del guion (§6.3). Un gesto que no está en `gestos` se quita con aviso;
# `puntos` y `raya` son reemplazos que cambian la lectura, así que también avisan.
TRADUCCION = {
    'omnivoice': dict(gestos={'risa': '[laughter]', 'suspiro': '[sigh]'}, enfasis='{}', puntos=',', raya=None,
                      quitar='', digitos=None),
    'voxcpm2': dict(gestos={}, enfasis='{}', puntos=None, raya=None, quitar='()*', digitos=None),
    'indextts': dict(gestos={}, enfasis='{}', puntos=None, raya=',', quitar='',
                     digitos='{motor} lee mal los dígitos; escríbelos en letras'),
    'cosyvoice3': dict(gestos={'risa': '[laughter]', 'suspiro': '[sigh]', 'respiro': '[breath]'},
                       enfasis='<strong>{}</strong>', puntos=None, raya=None, quitar='', digitos=None),
    # Qwen y Chatterbox: los gestos y el énfasis no se pueden pedir; los dígitos se leen mal (regla 13).
    'generico': dict(gestos={}, enfasis='{}', puntos=None, raya=None, quitar='',
                     digitos='{motor}: hay dígitos; escríbelos en letras (regla 13 de docs/formato-guion.md)'),
}


def usar_venv(venv: str, script: str = __file__) -> None:
    """Relanza `script` (por defecto este) con el python del venv, si no se está corriendo ya en él."""
    destino = AQUI / venv
    if Path(sys.prefix).resolve() == destino.resolve():
        return
    py = destino / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not py.exists():
        sys.exit(f'Falta {destino}. Ver "Instalación" en narration/README.md.')
    if os.name == 'nt':  # Windows no tiene exec: el padre espera al hijo y le deja el Ctrl+C
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        sys.exit(subprocess.call([str(py), script, *sys.argv[1:]]))
    os.execv(py, [str(py), script, *sys.argv[1:]])


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


def semilla_ronda(base: int, ronda: int) -> int:
    """Semilla de una ronda: la base en la primera generación y base + n en el reintento n.
    Si los reintentos repitieran la semilla, el bloque fallido saldría idéntico.

    >>> semilla_ronda(123, 0), semilla_ronda(123, 2)
    (123, 125)
    """
    return base + ronda


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


def segmentos(texto: str, estilo: str = 'experta') -> list[dict]:
    """Bloques a generar, cada uno con su silencio final, su estilo y su emoción (§5.1).

    Una línea en blanco deja PAUSA_PARRAFO. [pausa N] deja N segundos: si hay alguna entre dos bloques,
    mandan esas marcas (se suman) y no las líneas en blanco. [estilo:] y [emocion:] cortan el bloque: el
    cambio rige desde ese punto hasta el próximo de su tipo. Un corte a mitad de oración deja un aviso.

    >>> [(b['texto'], b['pausa']) for b in segmentos('Hola. Chao.')]
    [('Hola. Chao.', 0.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno.\\n\\nDos.')]
    [('Uno.', 0.6), ('Dos.', 0.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno. [pausa 1,5] Dos. [PAUSA 2s]')]
    [('Uno.', 1.5), ('Dos.', 2.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno.\\n\\n[pausa 0.2]\\n\\nDos.')]
    [('Uno.', 0.2), ('Dos.', 0.0)]
    >>> [(b['texto'], b['pausa']) for b in segmentos('Uno.\\n \\n[pausa 1] [pausa 2]\\nDos.')]
    [('Uno.', 3.0), ('Dos.', 0.0)]
    >>> [b['pausa'] for b in segmentos('a' * 200 + '. ' + 'b' * 200 + '.')]
    [0.25, 0.0]
    >>> segmentos('[pausa 1]\\n\\n')
    []
    >>> [(b['texto'], b['estilo'], b['emocion']) for b in segmentos('Uno. [estilo: dramatica] Dos. [emocion: miedo 0.4] Tres.')]
    [('Uno.', 'experta', None), ('Dos.', 'dramatica', None), ('Tres.', 'dramatica', ('miedo', 0.4))]
    >>> [(b['texto'], b['estilo']) for b in segmentos('Uno.', 'suave')]
    [('Uno.', 'suave')]
    >>> [b['avisos'] for b in segmentos('Hola, [estilo: intima] adiós.')]
    [['cambio de estilo a mitad de oración'], []]
    >>> [(b['texto'], b['emocion']) for b in segmentos('Uno.\\n\\n[emocion: triste]Dos. [emocion:]Tres.')]
    [('Uno.', None), ('Dos.', ('triste', 0.6)), ('Tres.', None)]
    """
    out: list[dict] = []
    marcas, hay_marca, blanco, pos = 0.0, False, False, 0
    actual, emo = estilo, None
    for m in [*MARCA_BLOQUE.finditer(texto), None]:
        fin = m.start() if m else len(texto)
        previo = texto[pos:fin]
        for t in trozos(previo):
            if out:
                out[-1]['pausa'] = marcas if hay_marca else PAUSA_PARRAFO if blanco else PAUSA_SEG
            out.append(dict(texto=t, pausa=0.0, estilo=actual, emocion=emo, avisos=[]))
            marcas, hay_marca, blanco = 0.0, False, False
        if m is None:
            break
        if m[1]:
            marcas, hay_marca = marcas + float(m[1].replace(',', '.')), True
        elif m[2] is not None or m[3] is not None:
            if out and previo.strip() and not re.search(r'[.!?…:]\s*$', previo):
                out[-1]['avisos'].append(f'cambio de {"estilo" if m[2] is not None else "emoción"} a mitad de oración')
            if m[2] is not None:
                actual = m[2]
            else:
                emo = (m[3].lower(), float(m[4].replace(',', '.')) if m[4] else 0.6) if m[3] else None
        else:
            blanco = True
        pos = m.end()
    if out and hay_marca:
        out[-1]['pausa'] = marcas
    return out


def etiquetas(texto: str) -> list[str]:
    """Marcas que el modelo pronunciaría. Las de la gramática (pausa, estilo, emoción, gestos, énfasis) no cuentan.

    >>> etiquetas('Hola [breath] <break time="1s"/> **ojo** (pausa) [pausa 1]')
    ['[breath]', '<break time="1s"/>', '**', '(pausa)']
    >>> etiquetas('Texto limpio, con pausa.\\n\\nY otro párrafo.')
    []
    >>> etiquetas('[risa] [estilo: dramatica] [emocion: triste 0.4] [enfasis]sí[/enfasis] [respiro]')
    []
    """
    return list(dict.fromkeys(ETIQUETA.findall(SIN_MARCAS.sub(' ', texto))))


def recortar(audio, sr: int, umbral: float = 0.01, margen: float = 0.08):
    """Quita el silencio y el ruido bajo que el modelo deja en los bordes de cada bloque (de
    0.5 s a más de 2 s), para que las pausas insertadas duren lo indicado. Deja `margen` s para
    no cortar consonantes.

    >>> import numpy as np
    >>> x = np.r_[np.zeros(1000), np.full(500, 0.5), np.zeros(1000)].astype(np.float32)
    >>> len(recortar(x, 1000))
    660
    >>> len(recortar(np.zeros(100, dtype=np.float32), 1000))
    0
    >>> cola = np.r_[np.full(500, 0.5), np.full(2000, 0.004), [0.012], np.zeros(10)].astype(np.float32)
    >>> len(recortar(cola, 1000))  # ruido de cola con un pico suelto: no es voz
    580
    """
    import numpy as np

    # RMS por ventanas de 20 ms: un pico suelto en el ruido de cola no cuenta como voz.
    n = max(1, int(sr * 0.02))
    k = len(audio) // n
    rms = np.sqrt((audio[:k * n].reshape(k, n).astype(np.float64) ** 2).mean(axis=1))
    voz = np.flatnonzero(rms > umbral)
    if not voz.size:
        return audio[:0]
    m = int(sr * margen)
    return audio[max(0, voz[0] * n - m):(voz[-1] + 1) * n + m]


def tramos_silencio(audio, sr: int, minimo: float, umbral: float = 0.01) -> list[float]:
    """Duración de cada silencio de al menos `minimo` s dentro del audio (RMS por ventanas de 20 ms).

    >>> import numpy as np
    >>> x = np.r_[np.full(500, 0.5), np.zeros(1500), np.full(300, 0.5), np.zeros(200), np.full(100, 0.5)]
    >>> tramos_silencio(x.astype(np.float32), 1000, 1.0), tramos_silencio(x.astype(np.float32), 1000, 0.2)
    ([1.5], [1.5, 0.2])
    """
    import numpy as np

    n = max(1, int(sr * 0.02))
    k = len(audio) // n
    quieto = np.sqrt((audio[:k * n].reshape(k, n).astype(np.float64) ** 2).mean(axis=1)) <= umbral
    tramos, corrida = [], 0
    for q in [*quieto, False]:
        if q:
            corrida += 1
        else:
            if corrida * n / sr >= minimo:
                tramos.append(round(corrida * n / sr, 2))
            corrida = 0
    return tramos


def leer_json(d: dict) -> tuple[str, str | None]:
    """Texto y estilo de un guion JSON. Cada elemento de `texto` es un párrafo. Un párrafo puede ser un
    objeto {"texto", "estilo", "emocion"}: equivale a anteponer esas marcas al texto.

    >>> leer_json({'texto': ['Uno.', 'Dos.'], 'estilo': 'suave'})
    ('Uno.\\n\\nDos.', 'suave')
    >>> leer_json({'texto': 'Solo uno.'})
    ('Solo uno.', None)
    >>> leer_json({'texto': ['Uno.', {'texto': 'Dos.', 'estilo': 'dramatica', 'emocion': 'miedo 0.4'}]})
    ('Uno.\\n\\n[estilo: dramatica][emocion: miedo 0.4]Dos.', None)
    """
    t = d['texto']
    if isinstance(t, str):
        return t, d.get('estilo')
    partes = []
    for p in t:
        if isinstance(p, dict):
            marcas = (f'[estilo: {p["estilo"]}]' if 'estilo' in p else '') + \
                (f'[emocion: {p["emocion"]}]' if 'emocion' in p else '')
            p = marcas + p['texto']
        partes.append(p)
    return '\n\n'.join(partes), d.get('estilo')


def normalizar(texto: str, idioma: str = 'es') -> list[str]:
    """Palabras comparables con lo que transcribe whisper: sin tildes, signos ni marcas del guion,
    y con las siglas juntas tanto deletreadas ("pe de efe") como en letras ("P D F"). En inglés no se
    normalizan siglas ni números (ver NUMEROS_EN).

    >>> normalizar('Sale en pe de efe, con su código cu erre. [pausa 1]')
    ['sale', 'en', 'pdf', 'con', 'su', 'codigo', 'qr']
    >>> normalizar('Criterios A, B, C, D, E. ¿Vídeo?')
    ['criterios', 'abcde', 'video']
    >>> normalizar('Te enviamos un video y ese día ve la o eme ese.')
    ['te', 'enviamos', 'un', 'video', 'y', 'ese', 'dia', 've', 'la', 'oms']
    >>> normalizar('Son 32 piezas, 7 especialidades y 100 recetas.')
    ['son', 'treinta', 'y', 'dos', 'piezas', 'siete', 'especialidades', 'y', 'cien', 'recetas']
    >>> normalizar('Me [risa] reí, [enfasis]sí[/enfasis] [estilo: dramatica]de verdad.')
    ['me', 'rei', 'si', 'de', 'verdad']
    >>> normalizar('It costs 7 dollars and twenty cents, [risa] really.', 'en')
    ['it', 'costs', 'really']
    >>> normalizar('It cost $7.20 and 5 percent more.', 'en')
    ['it', 'cost', 'more']
    """
    if idioma == 'en':
        return [w for w in re.findall(r'[a-z]+', SIN_MARCAS.sub(' ', texto).lower()) if w not in NUMEROS_EN]
    t = unicodedata.normalize('NFD', SIN_MARCAS.sub(' ', texto).lower())
    palabras = re.findall(r'\w+', ''.join(c for c in t if unicodedata.category(c) != 'Mn'))
    out: list[str] = []
    racha: list[str] = []

    def volcar() -> None:
        sueltas = all(len(w) == 1 for w in racha) and any(w not in 'aeiouy' for w in racha)
        if len(racha) >= 2 and (sueltas or LETRA_CLARA.intersection(racha)):
            out.append(''.join(LETRA.get(w, w) for w in racha))
        else:
            out.extend(racha)
        racha.clear()

    for w in palabras:
        if w.isdigit():
            volcar()
            out.extend(en_palabras(int(w)).split())
        elif w in LETRA or len(w) == 1:
            racha.append(w)
        else:
            volcar()
            out.append(w)
    volcar()
    return out


UNIDADES = [
    'cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once', 'doce',
    'trece', 'catorce', 'quince', 'dieciseis', 'diecisiete', 'dieciocho', 'diecinueve', 'veinte', 'veintiuno',
    'veintidos', 'veintitres', 'veinticuatro', 'veinticinco', 'veintiseis', 'veintisiete', 'veintiocho',
    'veintinueve',
]
DECENAS = {3: 'treinta', 4: 'cuarenta', 5: 'cincuenta', 6: 'sesenta', 7: 'setenta', 8: 'ochenta', 9: 'noventa'}


def en_palabras(n: int) -> str:
    """Número de 0 a 100 en palabras, sin tildes (whisper escribe "24" aunque se diga "veinticuatro").

    >>> en_palabras(7), en_palabras(24), en_palabras(32), en_palabras(40), en_palabras(2026)
    ('siete', 'veinticuatro', 'treinta y dos', 'cuarenta', '2026')
    """
    if n < 30:
        return UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return DECENAS[d] + (f' y {UNIDADES[u]}' if u else '')
    return 'cien' if n == 100 else str(n)


def fonetica(palabra: str) -> str:
    """Clave de cómo suena una palabra en español latinoamericano (seseo, yeísmo, b = v, h muda).

    >>> [fonetica(w) for w in ('click', 'stock', 'whatsapp', 'zoom', 'clinicae', 'clinicay', 'corriges')]
    ['clic', 'estoc', 'guasap', 'sum', 'clinicai', 'clinicai', 'corrijes']
    >>> fonetica('cuenta') == fonetica('cuento')
    False
    """
    w = palabra
    for a, b in (('wh', 'gu'), ('w', 'gu'), ('ck', 'c'), ('k', 'c'), ('q', 'c'), ('z', 's'), ('ce', 'se'),
                 ('ci', 'si'), ('ge', 'je'), ('gi', 'ji'), ('ll', 'y'), ('v', 'b'), ('h', ''), ('oo', 'u'),
                 ('ts', 's')):
        w = w.replace(a, b)
    w = re.sub(r'([^r])\1', r'\1', w)  # rr suena distinto de r
    w = re.sub(r'^s(?=[ptc])', 'es', w)
    return re.sub(r'(ae|y)$', lambda m: 'ai' if m[1] == 'ae' else 'i', w)


def comparar(esperado: list[str], oido: list[str]) -> list[tuple[str, str, str]]:
    """Diferencias (tipo, esperado, oído) entre dos listas de palabras.

    >>> comparar(normalizar('Cada segundo cuenta.'), normalizar('Cada segundo cuento.'))
    [('cambio', 'cuenta', 'cuento')]
    >>> comparar(['hola', 'mundo'], ['hola', 'mundo', 'braids'])
    [('sobra', '', 'braids')]
    >>> comparar(['hola', 'mundo'], ['mundo'])
    [('falta', 'hola', '')]

    Lo que suena igual no es un error: whisper escribe a su manera las palabras adaptadas.

    >>> comparar(['clic', 'en', 'estok', 'por', 'guasap', 'sin', 'zum'], ['click', 'en', 'stock', 'por', 'whatsapp', 'sin', 'zoom'])
    []
    >>> comparar(['de', 'pendiente', 'en', 'clinikai'], ['dependiente', 'en', 'clinica', 'y'])
    []
    """
    tipos = {'replace': 'cambio', 'delete': 'falta', 'insert': 'sobra'}
    return [
        (tipos[op], ' '.join(esperado[a1:a2]), ' '.join(oido[b1:b2]))
        for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, esperado, oido, autojunk=False).get_opcodes()
        if op != 'equal' and fonetica(''.join(esperado[a1:a2])) != fonetica(''.join(oido[b1:b2]))
    ]


def ritmo_raro(velocidades: list[float]) -> list[int]:
    """Índices de los párrafos cuyo ritmo se aleja de la mediana más que RITMO_TOLERANCIA.

    >>> ritmo_raro([3.0, 3.1, 2.9, 1.5, 3.0, 4.5])
    [3, 5]
    >>> ritmo_raro([2.0])
    []
    """
    med = statistics.median(velocidades)
    lo, hi = RITMO_TOLERANCIA
    return [i for i, v in enumerate(velocidades) if not lo * med <= v <= hi * med]


def normalizar_vec(v: list[float]) -> list[float]:
    """Vector de emoción de IndexTTS con el sesgo de su WebUI (§6.2). Si suma más de 0.8, se escala a 0.8.

    >>> [round(x, 3) for x in normalizar_vec([0.8, 0, 0, 0, 0, 0, 0, 0])]
    [0.75, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    >>> [round(x, 3) for x in normalizar_vec([0, 0, 0, 0.5, 0, 0, 0.3, 0])]
    [0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.206, 0.0]
    >>> round(sum(normalizar_vec([0.8] * 8)), 3)
    0.8
    """
    v = [a * b for a, b in zip(v, SESGO_INDEXTTS)]
    s = sum(v)
    return [x / s * 0.8 for x in v] if s > 0.8 else v


def traducir(texto: str, motor: str) -> tuple[str, list[str]]:
    """Texto que recibe el motor a partir del texto de un bloque, y los avisos de lo que quitó o reemplazó (§6.3).

    >>> traducir('despacio… y no había nadie', 'omnivoice')
    ('despacio, y no había nadie', ['omnivoice: "…" a mitad de oración se cambió por ","'])
    >>> traducir('me dijo que sí [risa] no lo podía creer', 'omnivoice')
    ('me dijo que sí [laughter] no lo podía creer', [])
    >>> traducir('me dijo que sí [risa] no lo podía creer', 'qwen-0.6b')[1]
    ['qwen-0.6b no soporta [risa]; se quitó']
    >>> traducir('es [enfasis]gratis[/enfasis] para siempre', 'cosyvoice3')
    ('es <strong>gratis</strong> para siempre', [])
    >>> traducir('revisa el texto — y guarda', 'indextts')
    ('revisa el texto, y guarda', ['indextts: "—" se cambió por "," (lo lee "menos")'])
    >>> traducir('Hola (amigo) *hoy*', 'voxcpm2')
    ('Hola amigo hoy', ['voxcpm2 no soporta "()*"; se quitaron'])
    >>> traducir('son 3 piezas', 'indextts')
    ('son 3 piezas', ['indextts lee mal los dígitos; escríbelos en letras'])
    >>> traducir('me dijo que sí [suspiro] y se fue', 'omnivoice')[0]
    'me dijo que sí [sigh] y se fue'
    >>> traducir('ya casi [respiro] llego', 'cosyvoice3')[0]
    'ya casi [breath] llego'
    >>> traducir('me dijo que sí [risa] no lo podía creer', 'voxcpm2')
    ('me dijo que sí no lo podía creer', ['voxcpm2 no soporta [risa]; se quitó'])
    >>> traducir('Hola (amigo) *hoy*', 'cosyvoice3')[0]
    'Hola (amigo) *hoy*'
    >>> traducir('esto — aquello', 'chatterbox')
    ('esto — aquello', [])
    >>> traducir('pagó 3 veces', 'chatterbox')[1]
    ['chatterbox: hay dígitos; escríbelos en letras (regla 13 de docs/formato-guion.md)']
    >>> traducir('es [enfasis]gratis[/enfasis] para siempre', 'qwen-0.6b')[0]
    'es gratis para siempre'
    """
    cfg = TRADUCCION[motor if motor in TRADUCCION else 'generico']
    avisos: list[str] = []

    def gesto(m: re.Match) -> str:
        marca = m[1].lower()
        if marca in cfg['gestos']:
            return cfg['gestos'][marca]
        avisos.append(f'{motor} no soporta [{marca}]; se quitó')
        return ''

    texto = ENFASIS.sub(lambda m: cfg['enfasis'].format(m[1]), GESTO.sub(gesto, texto))
    if cfg['quitar'] and re.search(f'[{re.escape(cfg["quitar"])}]', texto):
        avisos.append(f'{motor} no soporta "{cfg["quitar"]}"; se quitaron')
        texto = re.sub(f'[{re.escape(cfg["quitar"])}]', '', texto)
    if cfg['puntos'] and SUSPENSIVOS.search(texto):
        avisos.append(f'{motor}: "…" a mitad de oración se cambió por "{cfg["puntos"]}"')
        texto = SUSPENSIVOS.sub(cfg['puntos'], texto)
    if cfg['raya'] and '—' in texto:
        avisos.append(f'{motor}: "—" se cambió por "{cfg["raya"]}" (lo lee "menos")')
        texto = texto.replace('—', cfg['raya'])
    if cfg['digitos'] and re.search(r'\d', texto):
        avisos.append(cfg['digitos'].format(motor=motor))
    texto = re.sub(r'\s+([,.;:!?])', r'\1', re.sub(r'\s{2,}', ' ', texto)).strip()
    return texto, avisos


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

    m = MOTORES[a.modelo]
    usar_venv(m['venv'])  # desde aquí corre en el venv del motor: los avisos se imprimen una sola vez
    if a.voz:
        avisos_voz(a.voz, aprobadas(ESTILOS)[a.voz])

    import torch

    lote = a.lote or (lote_auto(torch.cuda.mem_get_info()[0] / 2**30, m['pesos']) if m.get('lote') else 1)
    semilla = a.semilla if a.semilla is not None else random.randrange(2**31)
    print(f'Semilla: {semilla}')
    if not m['comercial']:
        print(f'Aviso: {a.modelo} tiene licencia no comercial ({m["licencia"]}). Solo uso personal.')
    elif 'academic' in m['licencia']:
        print(f'Aviso: {a.modelo} es Apache-2.0, pero su model card dice "for academic purposes only" (sin aclarar). '
              'Ver docs/research/voicestudio-narracion/07.')

    # (nombre de salida o None, texto, estilo del JSON o None)
    guiones = [(None, a.texto, None)] if a.texto else []
    for f in a.archivo or []:
        if f.suffix == '.json':
            d = json.loads(f.read_text(encoding='utf-8'))
            guiones.append((d.get('id', f.stem), *leer_json(d)))
        else:
            guiones.append((f.stem, f.read_text(encoding='utf-8'), None))

    resultados = []
    for nombre, texto, estilo_json in guiones:
        estilo = a.estilo or estilo_json or ('neutral-en' if a.idioma == 'en' else 'experta')
        if estilo not in ESTILOS:
            sys.exit(f'Estilo desconocido "{estilo}" en {nombre}. Opciones: {", ".join(ESTILOS)}')
        if len(guiones) == 1 and a.salida:
            salida = a.salida
        else:
            wav = f'{nombre}-{a.modelo}.wav' if nombre else f'{a.modelo}-{estilo}.wav'
            salida = (a.salida or ROOT / 'out' / 'narration') / wav
        resultados.append(narrar(
            a.modelo, texto, estilo, a.ref, salida, lote, semilla, idioma=a.idioma, master=a.master, lufs=a.lufs,
        ))

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


def estirar(audio, sr: int, vel: float):
    """Cambia la velocidad sin cambiar el tono: ffmpeg atempo por tuberías."""
    import numpy as np

    if vel == 1.0 or not len(audio):
        return audio
    salida = subprocess.run(
        ['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', 'pipe:0',
         '-filter:a', f'atempo={vel}', '-f', 'f32le', 'pipe:1'],
        input=np.asarray(audio, dtype=np.float32).tobytes(), capture_output=True, check=True,
    ).stdout
    return np.frombuffer(salida, dtype=np.float32)


def escribir(g: dict) -> None:
    """Une los bloques con sus pausas, cada uno a la velocidad de su estilo, y guarda dónde empieza y
    termina cada bloque en el audio final (g['bloques'])."""
    import numpy as np
    import soundfile as sf

    sr, salida = g['sr'], g['salida']
    partes, g['bloques'], t = [], [], 0
    for voz, b, pb in zip(g['audios'], g['segs'], g['pb']):
        vel = pb['p']['velocidad']
        voz = estirar(voz, sr, vel)
        cola = estirar(np.zeros(int(sr * b['pausa']), dtype=np.float32), sr, vel)
        g['bloques'].append((b['texto'], t / sr, (t + len(voz)) / sr))
        t += len(voz) + len(cola)
        partes += [voz, cola]
    audio = np.concatenate(partes)

    salida.parent.mkdir(parents=True, exist_ok=True)
    if g['master'] == 'voz' and np.abs(audio).max(initial=0) > 1e-4:
        g['master_info'] = masterizar(audio, sr, salida, g['lufs'])
    else:
        sf.write(salida, audio, sr, subtype='PCM_24')
        g['master_info'] = {'modo': 'no'}


def _json_de_ffmpeg(stderr: str) -> dict:
    """loudnorm con print_format=json escribe su JSON al final de stderr."""
    return json.loads(stderr[stderr.rindex('{', 0, stderr.rindex('}')):stderr.rindex('}') + 1])


def _medir(ruta) -> tuple[float, float]:
    """Loudness integrado (LUFS) y pico real (dBTP) de un audio, con ebur128. Pasada 3 de la masterización."""
    veri = subprocess.run(
        ['ffmpeg', '-hide_banner', '-i', str(ruta), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
        capture_output=True, text=True, check=True,
    ).stderr
    return (float(re.search(r'^\s*I:\s+(-?[\d.]+) LUFS', veri, re.M)[1]),
            float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', veri)[1]))


def masterizar(audio, sr: int, salida: Path, lufs: float) -> dict:
    """Masterización 'voz' (§7.1): pasa-altos de 70 Hz y loudness lineal de dos pasadas hacia `lufs`, con techo de
    pico de −1.5 dBTP. Solo se limita la dinámica si el pico real no deja llegar a `lufs` (queda 'dynamic' y se
    avisa). Escribe WAV de 24 bits a la frecuencia nativa y devuelve lo medido."""
    import soundfile as sf

    crudo = salida.with_suffix('.crudo.wav')
    sf.write(crudo, audio, sr, subtype='FLOAT')
    base = f'highpass=f=70,loudnorm=I={lufs}'
    try:
        # Pasada 1: medir. Pasada 2: aplicar esa ganancia a la frecuencia nativa (loudnorm sobremuestrea a 192 kHz).
        med = _json_de_ffmpeg(subprocess.run(
            ['ffmpeg', '-hide_banner', '-i', str(crudo), '-af', f'{base}:TP=-1.5:LRA=11:print_format=json',
             '-f', 'null', '-'],
            capture_output=True, text=True, check=True,
        ).stderr)
        tp = -1.5
        for _ in range(3):
            filtro = (f'{base}:TP={tp}:LRA=11:linear=true:measured_I={med["input_i"]}:measured_TP={med["input_tp"]}'
                      f':measured_LRA={med["input_lra"]}:measured_thresh={med["input_thresh"]}'
                      f':offset={med["target_offset"]}:print_format=json,aresample={sr}')
            fin = _json_de_ffmpeg(subprocess.run(
                ['ffmpeg', '-hide_banner', '-y', '-i', str(crudo), '-af', filtro, '-c:a', 'pcm_s24le', str(salida)],
                capture_output=True, text=True, check=True,
            ).stderr)
            final, pico = _medir(salida)
            if pico <= -1.5:
                break
            # El limitador dinámico se pasa unas décimas: se baja el techo en lo que sobró, con un margen.
            tp = round(tp - (pico + 1.5 + 0.05), 2)
            print(f'Aviso: pico real {pico} dBTP sobre -1.5; se repite con techo {tp} dBTP.')
    finally:
        crudo.unlink(missing_ok=True)
    tipo = 'linear' if fin['normalization_type'] == 'linear' else 'dynamic'
    if tipo == 'dynamic':
        print(f'Aviso: el pico real no deja llegar a {lufs} LUFS con ganancia lineal; se normalizó con dinámica.')
    if abs(final - lufs) > 0.5 or pico > -1.5:
        print(f'Aviso: masterización fuera de criterio: {final} LUFS (objetivo {lufs}), pico real {pico} dBTP.')
    return {'modo': 'voz', 'lufs_objetivo': lufs, 'lufs_final': final, 'pico_real_final': pico, 'tipo': tipo,
            'techo_tp': tp}


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


def guardar_bloques(g: dict, indices) -> list[Path]:
    """Escribe cada bloque como un .wav propio para transcribirlo por separado: así whisper no
    se saltea tramos del audio largo ni reparte palabras entre párrafos vecinos."""
    import soundfile as sf

    carpeta = g['salida'].parent / 'whisper' / g['salida'].stem
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for i in indices:
        rutas.append(carpeta / f'{i + 1:02d}.wav')
        sf.write(rutas[-1], g['audios'][i], g['sr'])
    return rutas


def transcribir(wavs: list[Path], idioma: str) -> None:
    """Whisper en una sola pasada (el modelo se carga una vez); deja <wav>.json junto a cada audio."""
    carpetas: dict[Path, list[Path]] = {}
    for w in wavs:
        carpetas.setdefault(w.parent, []).append(w)
    print(f'Evaluando {len(wavs)} párrafo(s) con whisper {WHISPER_MODELO}...', flush=True)
    for carpeta, lista in carpetas.items():
        subprocess.run(
            ['whisper', *map(str, lista), '--model', WHISPER_MODELO, '--language', idioma,
             '--output_format', 'json', '--output_dir', str(carpeta)],
            check=True, capture_output=True,
        )


def revisar(g: dict) -> tuple[list[str], list[int]]:
    """Compara, párrafo por párrafo, la transcripción de whisper con el texto pedido (sin marcas).

    Whisper no oye entonación ni acento: marca palabras distintas, silencios largos dentro de
    un párrafo y ritmos raros. Devuelve las observaciones y los índices de los bloques afectados.
    """
    carpeta = g['salida'].parent / 'whisper' / g['salida'].stem
    problemas, fallidos, velocidades = [], set(), []
    for i, (b, voz) in enumerate(zip(g['segs'], g['audios'])):
        texto = b['texto']
        oido = json.loads((carpeta / f'{i + 1:02d}.json').read_text(encoding='utf-8'))['text']
        for tipo, esperado, dicho in comparar(normalizar(texto, g['idioma']), normalizar(oido, g['idioma'])):
            problemas.append(f'párrafo {i + 1}: {tipo} "{esperado}" -> "{dicho}"')
            fallidos.add(i)
        for d in tramos_silencio(voz, g['sr'], SILENCIO_MAX):
            problemas.append(f'párrafo {i + 1}: silencio de {d:.1f} s dentro del párrafo')
            fallidos.add(i)
        con_voz = len(voz) / g['sr'] - sum(tramos_silencio(voz, g['sr'], 0.2))  # sin las pausas de … y .
        velocidades.append(len(normalizar(texto, g['idioma'])) / max(con_voz, 0.1))
    med = statistics.median(velocidades)
    for i in ritmo_raro(velocidades):  # aviso: una lista o una pregunta se leen distinto a propósito
        problemas.append(f'aviso, párrafo {i + 1}: ritmo {velocidades[i]:.1f} palabras/s (mediana {med:.1f})')
    return problemas, sorted(fallidos)


if __name__ == '__main__':
    main()
