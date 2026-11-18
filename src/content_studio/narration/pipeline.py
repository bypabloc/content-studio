"""Generación de un guion: narrar, regenerar bloques sueltos y evaluar con whisper (con reintentos)."""

from __future__ import annotations

import random
import shutil
import sys
import time

from content_studio.narration.audio import escribir, recortar
from content_studio.narration.bloques import preparar_bloques
from content_studio.narration.estilos import EMOCIONES, ESTILOS
from content_studio.narration.evaluacion.revisar import guardar_bloques, revisar, semilla_ronda, transcribir
from content_studio.narration.motores.base import MotorTTS
from content_studio.narration.motores.registro import liberar_todo
from content_studio.narration.texto.segmentos import etiquetas, segmentos

# VRAM de Qwen por encima de los pesos: ~1.15 GiB la primera frase de ~300
# letras y ~1.3 GiB cada frase extra del lote. Más de 4 no mejora en 8 GB.
GIB_PRIMERA, GIB_POR_FRASE, MARGEN_GIB = 1.15, 1.3, 0.5
LOTE_MAX = 4
SIN_VOZ = 'el motor no produjo voz; si el párrafo termina sin . ? ! (corte a mitad de oración), puntúalo'


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


def narrar(motor: MotorTTS, texto, estilo, ref, salida, lote, semilla, idioma='es', master='voz', lufs=-16.0) -> dict:
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
    pb = preparar_bloques(motor, segs, ref)
    for i, p_ in enumerate(pb):
        for a in p_['avisos']:
            print(f'Aviso: párrafo {i + 1}: {a}')

    g = dict(
        salida=salida, segs=segs, pb=pb, estilo=estilo, p=ESTILOS[estilo], idioma=idioma, semilla=semilla,
        semillas=[], semilla_bloque=[None] * len(segs), audios=[], sr=0, bloques=[], tiempo_s=0.0,
        master=master, lufs=lufs, master_info=None,
    )  # fmt: skip
    regenerar(motor, g, range(len(segs)), lote, semilla)
    dur = g['bloques'][-1][2]
    print(
        f'{salida} ({dur:.1f} s, {motor.espec.nombre}, {estilo}, lote {lote}) | '
        f'generación {g["tiempo_s"]:.1f} s, {dur / g["tiempo_s"]:.2f}x tiempo real | '
        f'pico VRAM {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB',
        flush=True,
    )
    return g


def regenerar(motor: MotorTTS, g: dict, indices, lote: int, semilla: int) -> None:
    """(Re)genera los bloques indicados del guion `g` con la semilla de la ronda y reescribe su .wav.
    Qwen genera hasta `lote` bloques de la misma referencia por pasada; el resto de a uno."""
    import numpy as np

    tam = lote if motor.espec.lote else 1
    if not g['audios']:
        g['audios'] = [None] * len(g['segs'])
    g['semillas'].append(semilla)
    t0 = time.perf_counter()
    for grupo in lotes(list(indices), tam, lambda i: (g['pb'][i]['ref'], g['pb'][i]['p']['temperature'])):
        fijar(semilla)  # la semilla se fija antes de cada bloque o pasada (§4)
        audios, g['sr'] = motor.generar([g['pb'][i] for i in grupo], g['idioma'])
        for i, a_ in zip(grupo, audios, strict=False):
            g['audios'][i] = recortar(np.asarray(a_, dtype=np.float32), g['sr'])
            g['semilla_bloque'][i] = semilla
            if not len(g['audios'][i]) and SIN_VOZ not in g['pb'][i]['avisos']:
                print(f'Aviso: párrafo {i + 1}: {SIN_VOZ}')
                g['pb'][i]['avisos'].append(SIN_VOZ)
    g['tiempo_s'] += time.perf_counter() - t0
    escribir(g)


def evaluar(motor: MotorTTS, resultados: list[dict], lote: int, semilla: int, reintentos: int, idioma: str) -> None:
    if not shutil.which('whisper'):
        sys.exit('Falta el comando whisper (pip install openai-whisper); no se puede evaluar.')
    informe: dict[int, tuple[list[str], list[int]]] = {}  # guion -> (observaciones, bloques con error)
    pendientes = {k: list(range(len(g['segs']))) for k, g in enumerate(resultados)}  # guion -> bloques
    for ronda in range(reintentos + 1):  # noqa: B007  (ronda se usa después del bucle)
        liberar_todo()  # libera la VRAM para whisper
        transcribir([w for k, idx in pendientes.items() for w in guardar_bloques(resultados[k], idx)], idioma)
        for k in pendientes:
            informe[k] = revisar(resultados[k])
        pendientes = {k: informe[k][1] for k in pendientes if informe[k][1]}
        if not pendientes or ronda == reintentos:
            break
        n = sum(map(len, pendientes.values()))
        print(f'Reintento {ronda + 1}/{reintentos}: regenerando {n} párrafo(s) de {len(pendientes)} guion(es)...')
        for k, idx in pendientes.items():
            regenerar(motor, resultados[k], idx, lote, semilla_ronda(semilla, ronda + 1))

    for k, g in enumerate(resultados):
        problemas, fallidos = informe[k]
        g['evaluacion'] = {'rondas': ronda + 1, 'observaciones': problemas, 'ok': not fallidos}
        print(f'{"REVISAR" if fallidos else "OK     "} {g["salida"]}')
        for linea in problemas:
            print(f'          {linea}')
    revisar_n = sum(bool(f) for _, f in informe.values())
    print(f'{len(resultados) - revisar_n}/{len(resultados)} sin errores (los avisos de ritmo no cuentan).')
