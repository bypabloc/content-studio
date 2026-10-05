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
import difflib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import unicodedata
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
LETRA_CLARA = set(LETRA) - {'a', 'de', 'e', 'i', 'o', 'u', 'ye', 'te', 've', 'ese'}


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
    """Texto y estilo de un guion JSON. Cada elemento de `texto` es un párrafo.

    >>> leer_json({'texto': ['Uno.', 'Dos.'], 'estilo': 'suave'})
    ('Uno.\\n\\nDos.', 'suave')
    >>> leer_json({'texto': 'Solo uno.'})
    ('Solo uno.', None)
    """
    t = d['texto']
    return '\n\n'.join(t) if isinstance(t, list) else t, d.get('estilo')


def normalizar(texto: str) -> list[str]:
    """Palabras comparables con lo que transcribe whisper: sin tildes, signos ni [pausa N],
    y con las siglas juntas tanto deletreadas ("pe de efe") como en letras ("P D F").

    >>> normalizar('Sale en pe de efe, con su código cu erre. [pausa 1]')
    ['sale', 'en', 'pdf', 'con', 'su', 'codigo', 'qr']
    >>> normalizar('Criterios A, B, C, D, E. ¿Vídeo?')
    ['criterios', 'abcde', 'video']
    >>> normalizar('Te enviamos un video y ese día ve la o eme ese.')
    ['te', 'enviamos', 'un', 'video', 'y', 'ese', 'dia', 've', 'la', 'oms']
    >>> normalizar('Son 32 piezas, 7 especialidades y 100 recetas.')
    ['son', 'treinta', 'y', 'dos', 'piezas', 'siete', 'especialidades', 'y', 'cien', 'recetas']
    """
    t = unicodedata.normalize('NFD', MARCA_PAUSA.sub(' ', texto).lower())
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
    ap.add_argument(
        '--evaluar', action='store_true',
        help='al final transcribe cada salida con whisper y la compara, párrafo por párrafo, con el texto pedido',
    )
    ap.add_argument(
        '--reintentos', type=int, default=0,
        help='con --evaluar: rondas en las que se regeneran solo los párrafos con observaciones',
    )
    a = ap.parse_args()
    if a.reintentos and not a.evaluar:
        ap.error('--reintentos necesita --evaluar')

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

    resultados = []
    for nombre, texto, estilo_json in guiones:
        estilo = a.estilo or estilo_json or 'experta'
        if estilo not in ESTILOS:
            sys.exit(f'Estilo desconocido "{estilo}" en {nombre}. Opciones: {", ".join(ESTILOS)}')
        if len(guiones) == 1 and a.salida:
            salida = a.salida
        else:
            wav = f'{nombre}-{a.modelo}.wav' if nombre else f'{a.modelo}-{estilo}.wav'
            salida = (a.salida or ROOT / 'out' / 'narration') / wav
        resultados.append(narrar(a.modelo, repo, texto, estilo, a.ref, salida, lote))

    if not a.evaluar:
        return
    if not shutil.which('whisper'):
        sys.exit('Falta el comando whisper (pip install openai-whisper); no se puede evaluar.')
    informe: dict[int, tuple[list[str], list[int]]] = {}  # guion -> (observaciones, bloques con error)
    pendientes = {k: list(range(len(g['segs']))) for k, g in enumerate(resultados)}  # guion -> bloques
    for ronda in range(a.reintentos + 1):
        cargar_qwen.cache_clear()  # libera la VRAM para whisper
        cargar_chatterbox.cache_clear()
        torch.cuda.empty_cache()
        transcribir([w for k, idx in pendientes.items() for w in guardar_bloques(resultados[k], idx)])
        for k in pendientes:
            informe[k] = revisar(resultados[k])
        pendientes = {k: informe[k][1] for k in pendientes if informe[k][1]}
        if not pendientes or ronda == a.reintentos:
            break
        n = sum(map(len, pendientes.values()))
        print(f'Reintento {ronda + 1}/{a.reintentos}: regenerando {n} párrafo(s) de {len(pendientes)} guion(es)...')
        for k, idx in pendientes.items():
            regenerar(a.modelo, repo, resultados[k], idx, lote)

    for k, g in enumerate(resultados):
        problemas, fallidos = informe[k]
        print(f'{"REVISAR" if fallidos else "OK     "} {g["salida"]}')
        for linea in problemas:
            print(f'          {linea}')
    revisar_n = sum(bool(f) for _, f in informe.values())
    print(f'{len(resultados) - revisar_n}/{len(resultados)} sin errores (los avisos de ritmo no cuentan).')


def narrar(modelo, repo, texto, estilo, ref, salida, lote) -> dict:
    """Genera todos los bloques del texto y escribe el .wav. Devuelve lo necesario para
    evaluar y regenerar bloques sueltos."""
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

    g = {
        'salida': salida, 'segs': segs, 'p': p, 'wav_ref': wav_ref, 'texto_ref': texto_ref,
        'audios': [], 'sr': 0, 'bloques': [],
    }
    t0 = time.perf_counter()
    regenerar(modelo, repo, g, range(len(segs)), lote)
    total_s = time.perf_counter() - t0
    dur = g['bloques'][-1][2]
    print(
        f'{salida} ({dur:.1f} s, {modelo}, {estilo}, lote {lote}) | '
        f'generación {total_s:.1f} s, {dur / total_s:.2f}x tiempo real | '
        f'pico VRAM {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB',
        flush=True,
    )
    return g


def regenerar(modelo, repo, g: dict, indices, lote) -> None:
    """(Re)genera los bloques indicados del guion `g` y vuelve a escribir su .wav."""
    import numpy as np

    indices = list(indices)
    generar = generar_chatterbox if modelo == 'chatterbox' else generar_qwen
    audios, g['sr'] = generar(repo, [g['segs'][i][0] for i in indices], g['wav_ref'], g['texto_ref'], g['p'], lote)
    if not g['audios']:
        g['audios'] = [None] * len(g['segs'])
    for i, a_ in zip(indices, audios):
        g['audios'][i] = recortar(np.asarray(a_, dtype=np.float32), g['sr'])
    escribir(g)


def escribir(g: dict) -> None:
    """Une los bloques con sus pausas, aplica la velocidad del estilo y guarda dónde empieza
    y termina cada bloque en el audio final (g['bloques'])."""
    import numpy as np
    import soundfile as sf

    sr, vel, salida = g['sr'], g['p']['velocidad'], g['salida']
    partes, g['bloques'], t = [], [], 0
    for voz, (texto, seg) in zip(g['audios'], g['segs']):
        g['bloques'].append((texto, t / sr / vel, (t + len(voz)) / sr / vel))
        t += len(voz) + int(sr * seg)
        partes += [voz, np.zeros(int(sr * seg), dtype=np.float32)]
    audio = np.concatenate(partes)

    salida.parent.mkdir(parents=True, exist_ok=True)
    if vel == 1.0:
        sf.write(salida, audio, sr)
        return
    crudo = salida.with_suffix('.crudo.wav')
    sf.write(crudo, audio, sr)
    subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error', '-i', crudo, '-filter:a', f'atempo={vel}', salida],
        check=True,
    )
    crudo.unlink()


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


def transcribir(wavs: list[Path]) -> None:
    """Whisper en una sola pasada (el modelo se carga una vez); deja <wav>.json junto a cada audio."""
    carpetas: dict[Path, list[Path]] = {}
    for w in wavs:
        carpetas.setdefault(w.parent, []).append(w)
    print(f'Evaluando {len(wavs)} párrafo(s) con whisper {WHISPER_MODELO}...', flush=True)
    for carpeta, lista in carpetas.items():
        subprocess.run(
            ['whisper', *map(str, lista), '--model', WHISPER_MODELO, '--language', 'es',
             '--output_format', 'json', '--output_dir', str(carpeta)],
            check=True, capture_output=True,
        )


def revisar(g: dict) -> tuple[list[str], list[int]]:
    """Compara, párrafo por párrafo, la transcripción de whisper con el texto pedido.

    Whisper no oye entonación ni acento: marca palabras distintas, silencios largos dentro de
    un párrafo y ritmos raros. Devuelve las observaciones y los índices de los bloques afectados.
    """
    carpeta = g['salida'].parent / 'whisper' / g['salida'].stem
    problemas, fallidos, velocidades = [], set(), []
    for i, ((texto, _), voz) in enumerate(zip(g['segs'], g['audios'])):
        oido = json.loads((carpeta / f'{i + 1:02d}.json').read_text(encoding='utf-8'))['text']
        for tipo, esperado, dicho in comparar(normalizar(texto), normalizar(oido)):
            problemas.append(f'párrafo {i + 1}: {tipo} "{esperado}" -> "{dicho}"')
            fallidos.add(i)
        for d in tramos_silencio(voz, g['sr'], SILENCIO_MAX):
            problemas.append(f'párrafo {i + 1}: silencio de {d:.1f} s dentro del párrafo')
            fallidos.add(i)
        con_voz = len(voz) / g['sr'] - sum(tramos_silencio(voz, g['sr'], 0.2))  # sin las pausas de … y .
        velocidades.append(len(re.findall(r'\w+', texto)) / max(con_voz, 0.1))
    med = statistics.median(velocidades)
    for i in ritmo_raro(velocidades):  # aviso: una lista o una pregunta se leen distinto a propósito
        problemas.append(f'aviso, párrafo {i + 1}: ritmo {velocidades[i]:.1f} palabras/s (mediana {med:.1f})')
    return problemas, sorted(fallidos)


if __name__ == '__main__':
    main()
