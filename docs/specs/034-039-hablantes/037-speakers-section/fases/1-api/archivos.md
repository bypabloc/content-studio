# Spec 037, fase 1: archivos

### Crear

- `server/src/content_studio/api/routes/diarizations.py`.
- `server/src/content_studio/editor/from_diarization.py`.
- Tests espejo.
  - Verify: `uv run pytest -q`

### Modificar

- `server/src/content_studio/api/routes/editor.py` — `POST /editor/projects/from-diarization`.
- `server/src/content_studio/api/app.py` — registra la ruta.
- `client/src/shared/api/schema.d.ts` — se regenera.
  - Verify: `python -m devtools test-runner --type=typecheck`

### Solo lectura

- `server/src/content_studio/editor/store.py`, `ops.py` y `schema.py` — plantilla y marcadores.
