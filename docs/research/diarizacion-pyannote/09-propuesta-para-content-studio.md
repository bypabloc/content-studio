# 09. Propuesta para content-studio

> Insumo para la spec de diarización (`crear-spec`). Nada de esto está implementado ni medido todavía.

## 1. Flujo

```text
audio/video ──ffmpeg──► WAV 16 kHz mono (tmp del trabajo)
                         │
     ┌───────────────────┴───────────────────┐
     ▼ (turno de GPU 1)                       ▼ (turno de GPU 2, después)
faster-whisper (.venv-whisper)          pyannote community-1 (.venv-diarize)
words_payload → transcript.json         serialize() → diarization.json
     └───────────────────┬───────────────────┘
                         ▼  (stdlib, sin GPU, en server/src)
             assign_speakers + bloques por hablante
                         ▼
          transcript con speaker por palabra → subtítulos / editor / UI
```

* **Dos procesos, en secuencia**: cada uno toma el candado de `gpu_lock.py` por separado. Nunca los dos modelos a la vez ([turno-gpu](../../../.agents/rules/turno-gpu.md)).
* La unión es una función pura de `server/src/` que solo usa stdlib, con tests de caracterización sobre JSON fijos.

## 2. El motor (propuesta)

* **Receta** `pyannote-community-1`: Python 3.12, torch 2.11 cu128, `pyannote.audio==4.1.1`, `torchcodec==0.17.0` y los pesos con la revisión fijada ([02](02-versiones-e-instalacion.md) §3). Su librería va en `LIBRARIES` de `test_venvs.py`.
* **Script del motor**, que corre dentro de su venv:
  1. `os.environ['PYANNOTE_METRICS_ENABLED'] = '0'` y `HF_HUB_OFFLINE=1` antes de importar pyannote;
  2. `Pipeline.from_pretrained(<carpeta local>)` y `.cuda()` si hay GPU (en CPU es lento: avisar);
  3. `pipeline.embedding_batch_size = <medido>`;
  4. leer el WAV con `wave` y numpy y llamar con `{"waveform", "sample_rate"}`;
  5. `num_speakers`, `min_speakers` y `max_speakers` desde los parámetros del trabajo;
  6. el `hook` reporta progreso a la cola ([03](03-api-y-uso.md) §5);
  7. escribir `output.serialize()`, más `speaker_embeddings` si hacen falta, en `diarization.json`.
* Los audios de menos de ~3 s, o con un solo hablante pedido, no se diarizan ([05](05-rendimiento-y-vram.md) §6).
* **Factory Method**: no hace falta mientras haya un solo motor de diarización ([codigo-python](../../../.agents/rules/codigo-python.md)). Basta un módulo.

## 3. Superficie de producto (a definir en la spec)

* **Transcribir** con la opción «Identificar hablantes» y un campo «Número de hablantes» (vacío = automático), como en VoiceStudio.
* **Subtítulos** con el hablante en cada cue (`<v Hablante 1>` en VTT) y la opción de renombrar «Hablante 1» como «Ana».
* **Editor**: colorear la línea de tiempo por hablante y permitir corregir a mano: cambiar el hablante, crear uno nuevo y partir en el cursor.
* **Ajustes > Motores**: instalar «Diarización (pyannote)» con los pasos del token y las condiciones, y un error claro para el 401/403.
* Los textos van en el catálogo de tres idiomas ([textos-e-idioma](../../../.agents/rules/textos-e-idioma.md)).

## 4. Pruebas y mediciones (para la verificación final de la spec)

| Qué | Cómo |
| :--- | :--- |
| Unión palabra → hablante | TDD con JSON fijos: solape, hueco, `max_gap`, palabra sin `end`, sin turnos y una palabra suelta en medio |
| Telemetría apagada | Test del entorno del subproceso (`PYANNOTE_METRICS_ENABLED=0`) |
| Import del venv | `uv run pytest -m local` con `pyannote.audio` en `LIBRARIES` |
| torchcodec y FFmpeg en Windows | `import pyannote.audio` con el FFmpeg que detecta la app: ¿falla sin DLL compartidas? |
| VRAM y tiempo | Corridas reales con `gpu-turn run` de 5, 30 y 60 min con `embedding_batch_size` de 1, 4, 8 y 16. Pico con `torch.cuda.max_memory_allocated()` y con `nvidia-smi` |
| Calidad | El plan de [06](06-calidad-y-evaluacion.md) §4: DER y WDER sobre clips propios |

## 5. Pendientes antes de diseñar

1. Leer con sesión iniciada las condiciones completas de community-1 y el `config.yaml`: el `embedding_batch_size` y los `params` reales.
2. Confirmar si el paso `hf` de las recetas acepta un token del usuario para repositorios restringidos.
3. Confirmar si `import pyannote.audio` carga torchcodec al importar en Windows sin un FFmpeg *shared*.
4. Medir VRAM, tiempo y calidad (§4) y completar `vram_gb` y `size_gb` de la receta.
5. Decidir entre las opciones A, B y C de distribución ([07](07-licencias-privacidad-y-seguridad.md) §2) y registrar la decisión en `docs/process/WARNING/` si se elige B.
