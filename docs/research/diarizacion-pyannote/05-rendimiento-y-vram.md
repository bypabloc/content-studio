# 05. Rendimiento y VRAM

## 1. Velocidad publicada

| Fuente | Dato |
| :--- | :--- |
| README de pyannote (leída), H100 80 GB | community-1: **31 s por hora de audio** (AMI, archivos de ~1 h) y 37 s por hora (DIHARD 3, archivos de ~5 min) |
| [#1963](https://github.com/pyannote/pyannote-audio/issues/1963) (leída), RTX A5000, 4.0.4 | Un audio de 62 min tardó **~59 s** con community-1 |
| [#2050](https://github.com/pyannote/pyannote-audio/issues/2050) (leída), RTX 5060 Ti, rama con PR #2107 | 104× a 271× tiempo real en VoxConverse (con un parche que todavía no está fusionado) |
| arXiv 2509.26177 (leída por el agente), A6000, pyannote 3.1 | RTF medio de 45 (tiempo de audio / tiempo de proceso) |

* **Estimación para la RTX 4060 Laptop** (no medida): bastante más lenta que una H100. Del orden de 1 a 3 minutos por hora de audio con el audio en memoria. **Hay que medirlo** ([09](09-propuesta-para-content-studio.md)).
* En CPU, la etapa de embeddings es unas 20× más lenta que en una GPU de Apple (#2050, leída): en CPU puede tardar más que el audio mismo.

## 2. El pico de VRAM ([#1963](https://github.com/pyannote/pyannote-audio/issues/1963), abierto, leída)

* **Síntoma**: con un audio de 72 min, 4.0.3 llegó a **9,54 GB** de pico, contra 1,59 GB de 3.3.2. Otro usuario midió **10,53 GiB asignados y 12,09 GiB reservados** con 4.0.4, tanto con community-1 como con 3.1.
* **Causa** (diagnóstico del usuario con instrumentación): el pico ocurre en **una sola** llamada a `_embedding` con un lote grande (32 o 29 elementos de 10 s). Lo atribuye a que cuDNN elige otro algoritmo o espacio de trabajo para el último lote parcial. Las demás llamadas rondan 1,8 GB.
* **Solución alternativa** (medida por el mismo usuario):

```python
pipeline.embedding_batch_size = 4     # pico: 0,46 GiB asignados / 0,97 GiB reservados
```

* El constructor trae `embedding_batch_size=1`, pero el `config.yaml` del pipeline puede fijar otro valor (3.1 usa 32, leída en #2044). **Hay que fijarlo siempre de forma explícita** después de `from_pretrained` y medir el pico con `torch.cuda.max_memory_allocated()`.
* Con 8 GB y la regla de un modelo a la vez, el valor inicial recomendado está entre **4 y 8**. Se sube solo si la medición lo permite.
* Hasta entonces, `vram_gb` de la receta se completa con lo medido, no con lo publicado.

## 3. La etapa de embeddings lenta ([#1955](https://github.com/pyannote/pyannote-audio/issues/1955), leída)

* Con 4.0.2 y una RTX 4070, un audio de 5 minutos tardó **17,6 min**. Con el audio ya en memoria tardó **0,83 min** (21×).
* **Causa**: torchcodec anterior a 0.14 decodificaba desde el inicio del archivo hasta cada fragmento pedido, así que el costo crecía de forma cuadrática con la duración. Con 0.7, en un audio de 26 min, leer 10 s de FLAC en el minuto 25 tardaba 3 s. Con 0.17 tarda 3,5 ms ([torchcodec#1449](https://github.com/meta-pytorch/torchcodec/pull/1449), citado en el issue).
* **Qué hacer**: pasar siempre el audio en memoria ([03](03-api-y-uso.md) §4) y fijar torchcodec ≥ 0.14.

## 4. TF32 apagado en todo el proceso ([#2108](https://github.com/pyannote/pyannote-audio/issues/2108), abierto, leída)

* `Pipeline.__call__`, `Inference.__call__` e `Inference.crop` llaman a `fix_reproducibility(device)`, que pone `torch.backends.cuda.matmul.allow_tf32` y `torch.backends.cudnn.allow_tf32` en `False` y no los restaura.
* Si otro modelo corre en el mismo proceso, por ejemplo un ASR con torch, queda más lento desde la primera diarización.
* El mantenedor aceptó revisar un PR con un *context manager* (2026-11-24).
* **Para nosotros**: la diarización corre en su venv y en **su propio proceso**, como los demás motores (`common/process.py`). faster-whisper usa CTranslate2, así que no le afecta.

## 5. Audios largos

* La reconstrucción y el clustering crecen con la duración. Hay reportes de 3.x con caídas en audios de más de 5 a 8 horas (snippet).
* Con el pico de §2 controlado, una hora entra en la GPU según #1963 (10 GB por un lote grande, menos de 1 GB con lote 4).
* **Si hiciera falta partir** (más de unas 3 h, o sin VRAM): diarizar por trozos de 30 a 60 min con un solape de unos 30 s, y unir las etiquetas comparando `speaker_embeddings` con similitud coseno. Es complejo y fácil de equivocar: no se implementa hasta que un audio real lo exija (KISS).

## 6. Audios cortos

* Archivos de unos 5 s fallaban en 4.0.3 con `requested chunk ... resulted in N samples instead of the expected M`. Se resuelve con `preload=True` o con el audio en memoria ([#1969](https://github.com/pyannote/pyannote-audio/issues/1969), leída).
* Con voz de 1 o 2 palabras (~2 s) puede no salir ningún embedding válido: `Found speech but no valid (non-NaN) speaker embeddings could be generated` ([#1961](https://github.com/pyannote/pyannote-audio/issues/1961), leída). Un audio así se trata como **un solo hablante** sin diarizar.
* 4.1.0 corrige el fallo de VBx cuando se piden más hablantes que embeddings disponibles (leída, release 4.1.0).

## 7. Mejoras en camino (no fusionadas al 2026-11-24)

* PR #2048, #1996 y #2106 calculan el embedding **una vez por fragmento** en vez de una vez por hablante y fragmento. Dan el mismo DER en los 216 archivos de VoxConverse y son unas 2,2× más rápidos (leída, #2050).
* PR #2107 agrega un modo aproximado opcional, ~2,5× más rápido sobre lo anterior y con un DER casi igual.
* Al actualizar la receta, revisar si entraron en una versión.
