"""--evaluar: whisper transcribe cada bloque por separado y se revisan palabras, silencios y ritmo."""

from __future__ import annotations

import json
import statistics
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from content_studio.narration.evaluacion.comparar import comparar, normalizar

if TYPE_CHECKING:
    import numpy as np

# --evaluar: whisper transcribe la salida y se compara con el texto pedido.
WHISPER_MODELO = 'medium'  # small confundía palabras ("horarios" -> "cerrarios")
SILENCIO_MAX = 1.3  # criterio: un silencio más largo dentro de un párrafo es una pausa que nadie pidió
RITMO_TOLERANCIA = (0.7, 1.4)  # criterio: palabras/s del párrafo frente a la mediana del guion


def semilla_ronda(base: int, ronda: int) -> int:
    """Semilla de una ronda: la base en la primera generación y base + n en el reintento n.
    Si los reintentos repitieran la semilla, el bloque fallido saldría idéntico.

    >>> semilla_ronda(123, 0), semilla_ronda(123, 2)
    (123, 125)
    """
    return base + ronda


def tramos_silencio(audio: np.ndarray, sr: int, minimo: float, umbral: float = 0.01) -> list[float]:
    """Duración de cada silencio de al menos `minimo` s dentro del audio (RMS por ventanas de 20 ms).

    >>> import numpy as np
    >>> x = np.r_[np.full(500, 0.5), np.zeros(1500), np.full(300, 0.5), np.zeros(200), np.full(100, 0.5)]
    >>> tramos_silencio(x.astype(np.float32), 1000, 1.0), tramos_silencio(x.astype(np.float32), 1000, 0.2)
    ([1.5], [1.5, 0.2])
    """
    import numpy as np

    n = max(1, int(sr * 0.02))
    k = len(audio) // n
    quieto = np.sqrt((audio[: k * n].reshape(k, n).astype(np.float64) ** 2).mean(axis=1)) <= umbral
    tramos, corrida = [], 0
    for q in [*quieto, False]:
        if q:
            corrida += 1
        else:
            if corrida * n / sr >= minimo:
                tramos.append(round(corrida * n / sr, 2))
            corrida = 0
    return tramos


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


def guardar_bloques(g: dict, indices: Iterable[int]) -> list[Path]:
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
            [
                'whisper',
                *map(str, lista),
                '--model',
                WHISPER_MODELO,
                '--language',
                idioma,
                '--output_format',
                'json',
                '--output_dir',
                str(carpeta),
            ],
            check=True,
            capture_output=True,
        )


def revisar(g: dict) -> tuple[list[str], list[int]]:
    """Compara, párrafo por párrafo, la transcripción de whisper con el texto pedido (sin marcas).

    Whisper no oye entonación ni acento: marca palabras distintas, silencios largos dentro de
    un párrafo y ritmos raros. Devuelve las observaciones y los índices de los bloques afectados.
    """
    carpeta = g['salida'].parent / 'whisper' / g['salida'].stem
    problemas, fallidos, velocidades = [], set(), []
    for i, (b, voz) in enumerate(zip(g['segs'], g['audios'], strict=False)):
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
