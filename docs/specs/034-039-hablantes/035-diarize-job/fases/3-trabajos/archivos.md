# Spec 035, fase 3: archivos

### Crear

- `server/src/content_studio/diarization/cache.py`, `run.py`, `job_main.py` y `transcribe_speakers_main.py`.
- `server/src/content_studio/services/diarize.py` y `diarize_split.py`.
- `server/src/content_studio/cli/diarize.py`.
- Tests espejo de cada módulo.
- `docs/process/01-done/diarization.md` — ficha nueva del módulo: «Qué resuelve», «Qué hace hoy», «Dónde vive» e Historial.
  - Verify: `uv run pytest -q`

### Modificar

- `server/src/content_studio/db/schema.py` — migración `diarizations`.
- `server/src/content_studio/services/registry.py` — `diarize` y `diarize.split`.
- `server/src/content_studio/services/transcribe.py` — `diarize` y los parámetros de hablantes.
- `server/src/content_studio/cli/main.py` — `diarize`.
- `server/src/content_studio/messages/{es,en,pt}.json` — textos de 02 §5.
- `AGENTS.md` — una fila «Diarización» en la tabla de herramientas y el atajo `uv run studio diarize`.
  - Verify: `python -m devtools test-runner --type=all && python -m devtools agent-context`
