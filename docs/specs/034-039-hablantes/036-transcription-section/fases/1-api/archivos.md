# Spec 036, fase 1: archivos

### Crear

- `server/src/content_studio/api/routes/speakers.py`.
- `server/src/content_studio/diarization/transcript_text.py`.
- `server/tests/unit/src/content_studio/api/routes/test_speakers.py` y `server/tests/unit/src/content_studio/diarization/test_transcript_text.py`.
  - Verify: `uv run pytest -q`

### Modificar

- `server/src/content_studio/api/app.py` — registra la ruta.
- `server/src/content_studio/messages/{es,en,pt}.json` — errores de 02 §5.
- `client/src/shared/api/schema.d.ts` — se regenera.
  - Verify: `python -m devtools test-runner --type=i18n,typecheck`
