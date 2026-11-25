# 035: pyannote carga community-1 de su carpeta, sin red ni telemetría

- **Contexto**: la receta `pyannote` instala `pyannote/speaker-diarization-community-1` (repositorio con acceso restringido) en `models/community-1`. Pyannote 4.x puede descargar o enviar métricas durante un trabajo.
- **Elegida**: `Pipeline.from_pretrained` con la carpeta local; `PYANNOTE_METRICS_ENABLED=0` y `HF_HUB_OFFLINE=1` antes de importar pyannote; lote de embeddings 4 con `pipeline.embedding_batch_size = 4` (la cifra del diseño de la spec, que controla el pico de VRAM según la investigación 03 §7). La verificación de la familia `diarization` valida la forma de `turns.json` sobre un tono de 6 s, como pide AC-6; no mide voz.
- **Descartadas**: cargar por nombre de repositorio (descarga durante el trabajo y pide token); dejar el lote en 1 (pico de VRAM más alto en 8 GB).
- **Cómo revertir**: `server/src/content_studio/diarization/diarize_main.py` (variables de entorno y `embedding_batch_size`) y la rama `diarization` de `engines/verification.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/diarization/test_diarize_main.py server/tests/unit/src/content_studio/engines/test_verification.py -q` (con pyannote y torch falsos). **No probado con pyannote 4.1.1 real**: la corrida real necesita `.venv-diarize` instalado y el acceso de community-1. Antes de `main`: `gpu-turn run` con un audio real y `verify_engine('pyannote')` (FV).
- **Pendiente**: la corrida real con pyannote 4.1.1 queda en la verificación final de la 035.
