# 04. Integración con faster-whisper

## 1. Entradas

* **Transcripción** (ya existe, `words_payload` en [transcribe_main.py](../../../server/src/content_studio/transcription/transcribe_main.py)):
  `{"segments": [{"start", "end", "text", "words": [{"start", "end", "word", "probability"}]}]}`.
* **Diarización** (`output.serialize()`, [03](03-api-y-uso.md) §2): listas `diarization` y `exclusive_diarization` de `{"start", "end", "speaker"}`.

Las dos son JSON. La unión se escribe en `server/src/` con stdlib, sin torch, y se prueba con TDD sin GPU.

## 2. Cómo lo hace WhisperX (leída, [`whisperx/diarize.py`](https://github.com/m-bain/whisperX/blob/main/whisperx/diarize.py), BSD-2-Clause, © 2024 Max Bain)

* `DiarizationPipeline` carga community-1 por defecto, pasa el audio en memoria (`{"waveform", "sample_rate"}`) y toma `output.speaker_diarization`, **no** la exclusiva.
* `assign_word_speakers`:
  1. Ordena los turnos por inicio y busca los candidatos con `np.searchsorted` (un «interval tree» simple: ~228× más rápido en audios de 3 h, según su docstring).
  2. Para cada **segmento** y cada **palabra**, suma la intersección `min(fin) - max(inicio)` con cada turno, por hablante, y elige el máximo.
  3. Si no hay intersección y `fill_nearest=True` (por defecto `False`), toma el hablante del turno cuyo **punto medio** está más cerca del punto medio de la palabra.
  4. Si la palabra no tiene `start`, la salta. Si no tiene `end`, usa `start`.
* Con `fill_nearest=False`, las palabras en huecos se quedan **sin hablante**.

## 3. Por qué la salida exclusiva

* La diarización normal tiene solapes: dos hablantes a la vez. Una palabra que cae ahí la gana el que más tiempo cubre, lo que no siempre es correcto.
* La exclusiva deja solo el hablante más probable en cada instante. Es la que pyannote recomienda para casar con transcripciones (CHANGELOG 4.0.0, leída).
* La normal conserva su uso: **marcar** las palabras en zona de solape, por ejemplo para no usar ese tramo como referencia de clonación de voz (regla de VoiceStudio, [nota anterior](../voicestudio-narracion/herramientas/07-diarizacion.md) §3).

## 4. Algoritmo propuesto (propuesta, no ejecutado)

```python
from __future__ import annotations

from bisect import bisect_left


def assign_speakers(words: list[dict], turns: list[dict], max_gap: float = 1.0) -> list[dict]:
    """Agrega 'speaker' a cada palabra: el turno con más solape o, en un hueco, el más cercano.

    `turns` es la diarización exclusiva ordenada por inicio. Una palabra a más de `max_gap` segundos
    de cualquier turno queda con speaker None.
    """
    starts = [t['start'] for t in turns]
    out = []
    for w in words:
        start, end = w['start'], max(w['end'], w['start'])
        i = bisect_left(starts, end)          # turnos que empiezan antes de que termine la palabra
        overlap: dict[str, float] = {}
        for t in turns[max(0, i - 8):i]:      # exclusiva: sin solapes, alcanzan pocos vecinos
            inter = min(t['end'], end) - max(t['start'], start)
            if inter > 0:
                overlap[t['speaker']] = overlap.get(t['speaker'], 0.0) + inter
        speaker = max(overlap, key=overlap.get) if overlap else _nearest(turns, i, start, end, max_gap)
        out.append({**w, 'speaker': speaker})
    return out


def _nearest(turns: list[dict], i: int, start: float, end: float, max_gap: float) -> str | None:
    """Hablante del turno vecino más cercano (distancia entre bordes, no entre puntos medios)."""
    best, dist = None, max_gap
    for t in turns[max(0, i - 1):i + 1]:
        d = max(t['start'] - end, start - t['end'], 0.0)
        if d <= dist:
            best, dist = t['speaker'], d
    return best
```

Diferencias con WhisperX, a propósito:

* Usa la **exclusiva**: un instante tiene un solo dueño.
* En un hueco, mide la **distancia entre bordes** y no entre puntos medios. Un turno largo con el punto medio lejos puede estar pegado a la palabra.
* **`max_gap`**: una palabra aislada en un silencio largo no se asigna a ciegas.
* La ventana `i - 8` es una heurística para turnos sin solape. Un test de caracterización debe compararla contra la búsqueda completa.

## 5. Agrupar en frases por hablante (propuesta)

1. Recorrer las palabras en orden y **cortar un bloque** cuando cambia el hablante.
2. **Absorber las palabras sueltas**: una palabra de otro hablante entre dos del mismo, sin pausa, suele ser un error de tiempos y se reasigna. VoiceStudio lo hace con las respuestas de una palabra que no son oración propia ([nota anterior](../voicestudio-narracion/herramientas/07-diarizacion.md) §3).
3. **Realinear por puntuación** (opcional, idea de whisper-diarization): si una oración termina con `.` `?` `!` y la mayoría de sus palabras es de un hablante, toda la oración pasa a ese hablante. Se mide con WDER antes de dejarla activa ([06](06-calidad-y-evaluacion.md)).
4. Para subtítulos, los bloques se cortan además por duración y caracteres, como ya hacen los subtítulos del proyecto. Cada cue lleva su hablante: `[Hablante 1] Texto…` en SRT, o `<v Hablante 1>Texto…` en WebVTT, que tiene etiqueta de voz nativa.

## 6. Desfase de tiempos de Whisper

* Los tiempos por palabra de faster-whisper salen de la atención cruzada y pueden correrse decenas o cientos de milisegundos en los cambios de turno. WhisperX lo corrige con alineación forzada wav2vec2 y trae un modelo para español (snippet).
* La salida exclusiva y la asignación por solape absorben gran parte del desfase. **Se agrega alineación solo si la evaluación muestra errores en los bordes de turno**: costaría otro modelo y otro paso de GPU.
* `vad_filter=True` (Silero) quita silencios de la transcripción, pero no cambia los tiempos absolutos de las palabras. Los dos JSON quedan en el mismo eje de tiempo del archivo original.
* La diarización debe recibir **el mismo audio** que se transcribió (mismo inicio y mismo recorte). Si el limpiador de silencios recorta, se diariza el audio ya recortado o se ajustan los tiempos.

## 7. Errores frecuentes al integrar

| Problema | Causa | Qué hacer |
| :--- | :--- | :--- |
| Una palabra de cada pocas sin hablante | Huecos entre turnos con `fill_nearest=False` | Usar el más cercano dentro de `max_gap` |
| Dos personas detectadas como una | Voces parecidas o un número de hablantes no fijado | Pedir `num_speakers` o `min_speakers` en la UI; probar `Fb` |
| Una persona partida en dos | Cambios de micrófono o de ambiente | `max_speakers`, o unir etiquetas con embeddings ([03](03-api-y-uso.md) §8) |
| El hablante cambia en mitad de una palabra | Turnos finos contra palabras largas | Asignar por palabra, nunca por segmento completo de Whisper |
| Etiquetas distintas entre partes de un audio largo | Cada llamada numera desde `SPEAKER_00` | Mapear con similitud de `speaker_embeddings` |
