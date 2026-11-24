# Spec 038, fase 1: archivos

### Modificar

- `server/src/content_studio/subtitles/segment.py`, `document.py`, `sources.py`, `create_main.py`, `ass.py`, `formats.py` y `export.py`.
- `server/src/content_studio/services/subtitles_create.py` — parámetros nuevos.
- `server/src/content_studio/api/routes/subtitles.py` — `from-transcript` con hablantes y `speaker_labels`.
- Tests espejo y `server/tests/integration/test_characterization.py`.
- `client/src/shared/api/schema.d.ts` — se regenera.
  - Verify: `uv run pytest -q && python -m devtools test-runner --type=typecheck`

### Solo lectura

- `server/src/content_studio/diarization/run.py` y `assign.py` (035).
