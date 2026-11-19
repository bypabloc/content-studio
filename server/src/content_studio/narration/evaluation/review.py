"""--evaluate: whisper transcribe cada bloque por separado y se revisan palabras, silencios y ritmo."""

from __future__ import annotations

import json
import statistics
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from content_studio.narration.evaluation.compare import compare, normalize

if TYPE_CHECKING:
    import numpy as np

# --evaluate: whisper transcribe la salida y se compara con el texto pedido.
WHISPER_MODEL = 'medium'  # small confundía palabras ("horarios" -> "cerrarios")
SILENCE_MAX = 1.3  # criterio: un silencio más largo dentro de un párrafo es una pausa que nadie pidió
RHYTHM_TOLERANCE = (0.7, 1.4)  # criterio: palabras/s del párrafo frente a la mediana del guion


def seed_round(base: int, attempt: int) -> int:
    """Semilla de una ronda: la base en la primera generación y base + n en el reintento n.
    Si los reintentos repitieran la semilla, el bloque fallido saldría idéntico.

    >>> seed_round(123, 0), seed_round(123, 2)
    (123, 125)
    """
    return base + attempt


def spans_silence(audio: np.ndarray, sr: int, minimum: float, threshold: float = 0.01) -> list[float]:
    """Duración de cada silencio de al menos `minimo` s dentro del audio (RMS por ventanas de 20 ms).

    >>> import numpy as np
    >>> x = np.r_[np.full(500, 0.5), np.zeros(1500), np.full(300, 0.5), np.zeros(200), np.full(100, 0.5)]
    >>> spans_silence(x.astype(np.float32), 1000, 1.0), spans_silence(x.astype(np.float32), 1000, 0.2)
    ([1.5], [1.5, 0.2])
    """
    import numpy as np

    n = max(1, int(sr * 0.02))
    k = len(audio) // n
    still = np.sqrt((audio[: k * n].reshape(k, n).astype(np.float64) ** 2).mean(axis=1)) <= threshold
    spans, run = [], 0
    for q in [*still, False]:
        if q:
            run += 1
        else:
            if run * n / sr >= minimum:
                spans.append(round(run * n / sr, 2))
            run = 0
    return spans


def rhythm_odd(speeds: list[float]) -> list[int]:
    """Índices de los párrafos cuyo ritmo se aleja de la mediana más que RITMO_TOLERANCIA.

    >>> rhythm_odd([3.0, 3.1, 2.9, 1.5, 3.0, 4.5])
    [3, 5]
    >>> rhythm_odd([2.0])
    []
    """
    med = statistics.median(speeds)
    lo, hi = RHYTHM_TOLERANCE
    return [i for i, v in enumerate(speeds) if not lo * med <= v <= hi * med]


def save_blocks(g: dict, indices: Iterable[int]) -> list[Path]:
    """Escribe cada bloque como un .wav propio para transcribirlo por separado: así whisper no
    se saltea tramos del audio largo ni reparte palabras entre párrafos vecinos."""
    import soundfile as sf

    folder = g['output'].parent / 'whisper' / g['output'].stem
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in indices:
        paths.append(folder / f'{i + 1:02d}.wav')
        sf.write(paths[-1], g['audios'][i], g['sr'])
    return paths


def transcribe(wavs: list[Path], language: str) -> None:
    """Whisper en una sola pasada (el modelo se carga una vez); deja <wav>.json junto a cada audio."""
    folders: dict[Path, list[Path]] = {}
    for w in wavs:
        folders.setdefault(w.parent, []).append(w)
    print(f'Evaluating {len(wavs)} paragraph(s) with whisper {WHISPER_MODEL}...', flush=True)
    for folder, items in folders.items():
        subprocess.run(
            [
                'whisper',
                *map(str, items),
                '--model',
                WHISPER_MODEL,
                '--language',
                language,
                '--output_format',
                'json',
                '--output_dir',
                str(folder),
            ],
            check=True,
            capture_output=True,
        )


def review(g: dict) -> tuple[list[str], list[int]]:
    """Compara, párrafo por párrafo, la transcripción de whisper con el texto pedido (sin marcas).

    Whisper no oye entonación ni acento: marca palabras distintas, silencios largos dentro de
    un párrafo y ritmos raros. Devuelve las observaciones y los índices de los bloques afectados.
    """
    folder = g['output'].parent / 'whisper' / g['output'].stem
    problems, failed, speeds = [], set(), []
    for i, (b, voice) in enumerate(zip(g['secs'], g['audios'], strict=False)):
        text = b['text']
        hearing = json.loads((folder / f'{i + 1:02d}.json').read_text(encoding='utf-8'))['text']
        for kind, expected, said in compare(normalize(text, g['language']), normalize(hearing, g['language'])):
            problems.append(f'paragraph {i + 1}: {kind} "{expected}" -> "{said}"')
            failed.add(i)
        for d in spans_silence(voice, g['sr'], SILENCE_MAX):
            problems.append(f'paragraph {i + 1}: {d:.1f} s of silence inside the paragraph')
            failed.add(i)
        with_voice = len(voice) / g['sr'] - sum(spans_silence(voice, g['sr'], 0.2))  # sin las pausas de … y .
        speeds.append(len(normalize(text, g['language'])) / max(with_voice, 0.1))
    med = statistics.median(speeds)
    for i in rhythm_odd(speeds):  # aviso: una lista o una pregunta se leen distinto a propósito
        problems.append(f'notice, paragraph {i + 1}: rhythm {speeds[i]:.1f} words/s (median {med:.1f})')
    return problems, sorted(failed)
