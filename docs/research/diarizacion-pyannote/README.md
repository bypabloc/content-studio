# Diarización con pyannote.audio 4.x y community-1

> Investigación del 2026-11-24. Cómo identificar **quién habla y cuándo** en un audio, después de transcribirlo con faster-whisper, usando [pyannote.audio](https://github.com/pyannote/pyannote-audio) 4.x y el modelo abierto [`pyannote/speaker-diarization-community-1`](https://huggingface.co/pyannote/speaker-diarization-community-1). Es la **investigación principal de diarización** del proyecto y reemplaza como referencia a [la nota sobre VoiceStudio](../voicestudio-narracion/herramientas/07-diarizacion.md). El equipo es una RTX 4060 Laptop de 8 GB en Windows 11.

## Respuesta corta

* **Qué usar**: `pyannote.audio==4.1.1` (Python ≥ 3.11) con `speaker-diarization-community-1`, en un venv propio con Python 3.12, ejecutado **después** de faster-whisper y en otro proceso.
* **Cómo unir con la transcripción**: usar `output.exclusive_speaker_diarization`, que tiene un solo hablante activo a la vez, y asignar cada palabra de faster-whisper al hablante con más solapamiento temporal. Si la palabra cae en un hueco, se usa el turno más cercano ([04](04-integracion-con-faster-whisper.md)).
* **Las cinco trampas que hay que evitar** (todas verificadas en el código o en issues):
  1. **Telemetría activada por defecto**: pyannote envía la duración de cada archivo y el número de hablantes a `otel.pyannote.ai`. Se apaga con `PYANNOTE_METRICS_ENABLED=0` ([07](07-licencias-privacidad-y-seguridad.md)).
  2. **Pico de VRAM de ~10 GB** en la etapa de embeddings con lotes grandes. Se evita con `pipeline.embedding_batch_size = 4` o un valor parecido ([05](05-rendimiento-y-vram.md)).
  3. **Leer desde archivo es lento** (21× en un caso real) con torchcodec < 0.14. Hay que pasar el audio ya cargado en memoria (`{"waveform": ..., "sample_rate": ...}`) o usar `preload=True` ([05](05-rendimiento-y-vram.md)).
  4. **TF32 se apaga en todo el proceso** en cada llamada. Por eso la diarización corre en su propio proceso ([05](05-rendimiento-y-vram.md)).
  5. **El repositorio de pesos está restringido** (*gated*): el usuario acepta condiciones en Hugging Face y usa un token una vez. Después todo funciona sin conexión desde una carpeta local ([03](03-api-y-uso.md), [07](07-licencias-privacidad-y-seguridad.md)).
* **Licencias**: código MIT y pesos CC-BY-4.0. Se permite el uso comercial con atribución ([07](07-licencias-privacidad-y-seguridad.md)).
* **Qué falta medir en este equipo**: VRAM y velocidad reales en la RTX 4060, y calidad en español con audios propios ([09](09-propuesta-para-content-studio.md)).

## Índice

| # | Capítulo | Contenido |
| :--- | :--- | :--- |
| 01 | [Panorama y elección](01-panorama-y-eleccion.md) | Alternativas evaluadas (WhisperX, NeMo, sherpa-onnx, DiariZen…) y por qué community-1 |
| 02 | [Versiones e instalación](02-versiones-e-instalacion.md) | Versiones de pyannote y torchcodec, dependencias, FFmpeg en Windows, receta propuesta |
| 03 | [API y uso](03-api-y-uso.md) | `Pipeline.from_pretrained`, `DiarizeOutput`, número de hablantes, progreso, audio en memoria, uso offline, hiperparámetros, embeddings |
| 04 | [Integración con faster-whisper](04-integracion-con-faster-whisper.md) | Asignar palabras a hablantes, código de WhisperX, propuesta propia, solapes, subtítulos con hablante |
| 05 | [Rendimiento y VRAM](05-rendimiento-y-vram.md) | Velocidad publicada, pico de VRAM y su arreglo, lectura lenta, TF32, audios largos y cortos |
| 06 | [Calidad y evaluación](06-calidad-y-evaluacion.md) | DER publicado, español, métricas (DER, JER, WDER, cpWER) y plan de evaluación propio |
| 07 | [Licencias, privacidad y seguridad](07-licencias-privacidad-y-seguridad.md) | MIT y CC-BY-4.0, acceso restringido, atribución, telemetría, ejecución remota desde `config.yaml` |
| 08 | [Problemas conocidos](08-problemas-conocidos.md) | Issues de pyannote 4.x con su estado y la solución alternativa |
| 09 | [Propuesta para content-studio](09-propuesta-para-content-studio.md) | Receta, proceso, flujo con faster-whisper, turno de la GPU, pruebas y pendientes para la spec |

## Cómo leer este documento

* **(leída)**: la fuente primaria se abrió y se citó: código en `develop`, CHANGELOG, PyPI, issues de GitHub o la tarjeta del modelo.
* **(snippet)**: dato visto solo en un resultado de búsqueda o en una fuente secundaria.
* **no verificado**: no se pudo confirmar. Antes de usarlo se mide o se lee la fuente.
* **Propuesta**: diseño o código escrito para este proyecto que todavía no se ejecutó.

Las versiones y fechas de PyPI, el CHANGELOG, los releases de GitHub, el código de `speaker_diarization.py` y `core/pipeline.py` (rama `develop`), los issues citados y `whisperx/diarize.py` se leyeron directamente el 2026-11-24. La tarjeta del modelo y su `config.yaml` piden sesión en Hugging Face (HTTP 401 sin token): lo que se dice de ellas viene de la tarjeta pública y del README del repositorio.
