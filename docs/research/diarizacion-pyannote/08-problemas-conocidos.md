# 08. Problemas conocidos (pyannote 4.x)

Todos los issues se leyeron el 2026-11-24. «Abierto» significa sin arreglo publicado.

| Issue | Qué pasa | Estado | Qué hacer |
| :--- | :--- | :--- | :--- |
| [#1963](https://github.com/pyannote/pyannote-audio/issues/1963) | Pico de 9,5 a 12 GB de VRAM en la etapa de embeddings con lotes de 29 a 32 | Abierto | `pipeline.embedding_batch_size = 4` (pico de 0,46 GiB) ([05](05-rendimiento-y-vram.md) §2) |
| [#1955](https://github.com/pyannote/pyannote-audio/issues/1955) | Embeddings muy lentos: 17,6 min para un audio de 5 min | Abierto | Audio en memoria y torchcodec ≥ 0.14 ([05](05-rendimiento-y-vram.md) §3) |
| [#2108](https://github.com/pyannote/pyannote-audio/issues/2108) | Apaga TF32 en todo el proceso en cada llamada | Abierto (PR aceptado en principio) | Diarizar en un proceso propio |
| [#1969](https://github.com/pyannote/pyannote-audio/issues/1969) | Archivos de ~5 s fallan con `requested chunk ... samples` | Cerrado sin arreglo | `preload=True` o audio en memoria |
| [#1961](https://github.com/pyannote/pyannote-audio/issues/1961) | 1 o 2 palabras no generan embeddings válidos (NaN) | Cerrado | Tratar como un solo hablante |
| [#1987](https://github.com/pyannote/pyannote-audio/issues/1987) | Habla solapada asignada a uno de los dos hablantes | Cerrado sin respuesta | Marcar los solapes con la salida normal y no prometer más |
| [#2032](https://github.com/pyannote/pyannote-audio/issues/2032) | 4.0.6 devolvía un generador y rompía WhisperX | Cerrado: 4.0.6 retirada, 4.0.7 lo corrige | No usar 4.0.6 |
| [#1928](https://github.com/pyannote/pyannote-audio/issues/1928) | `for turn, speaker in annotation` da `TypeError` | Cerrado | `pyannote.core>=6.0.1` o `itertracks(yield_label=True)` |
| [#1976](https://github.com/pyannote/pyannote-audio/issues/1976), [#1974](https://github.com/pyannote/pyannote-audio/issues/1974) | `torch==2.8.0` fijado en 4.0.2 y 4.0.3 chocaba con GPU Blackwell y torch 2.9. El *segfault* aparece con parejas torch/torchcodec incompatibles | Cerrado; 4.0.4 relaja la fijación | Respetar la tabla de compatibilidad ([02](02-versiones-e-instalacion.md) §2) |
| [#1940](https://github.com/pyannote/pyannote-audio/issues/1940), [torchcodec#1006](https://github.com/meta-pytorch/torchcodec/issues/1006) | `Could not load libtorchcodec`: no encuentra las DLL de FFmpeg | Cerrado; en Windows se siguió reportando en 2026-01 | FFmpeg *shared* y `os.add_dll_directory`, o evitar decodificar con audio en memoria |
| [#2044](https://github.com/pyannote/pyannote-audio/issues/2044) | Cargar 3.1 en pyannote 4.x pide acceso a community-1 por el PLDA | Abierto; el mantenedor recomienda usar pipelines viejos con versiones viejas | Usar community-1 |
| [#2034](https://github.com/pyannote/pyannote-audio/issues/2034) | En 3.x, `PYANNOTE_CACHE` pisa `HF_HUB_CACHE` y falla sin conexión | Abierto (afecta a 3.x) | En 4.x, caché de Hugging Face o carga desde carpeta local |
| [#2000](https://github.com/pyannote/pyannote-audio/issues/2000) | Un `config.yaml` malicioso ejecuta código al cargar | Abierto | Solo community-1 con la revisión fijada ([07](07-licencias-privacidad-y-seguridad.md) §5) |
| [#1960](https://github.com/pyannote/pyannote-audio/issues/1960) | `Model.from_pretrained` falla con `weights_only=True` de `torch.load` | Cerrado | Usar 4.0.3 o posterior |
| [#2050](https://github.com/pyannote/pyannote-audio/issues/2050) | Calcula embeddings una vez por hablante y fragmento: ~2× de trabajo de más | Abierto, con PR | Esperar la fusión ([05](05-rendimiento-y-vram.md) §7) |

## Telemetría (no es un issue: es el valor por defecto)

`metrics_enabled: true` en `telemetry/config.yaml`. Hay que apagarla con `PYANNOTE_METRICS_ENABLED=0` ([07](07-licencias-privacidad-y-seguridad.md) §4).
