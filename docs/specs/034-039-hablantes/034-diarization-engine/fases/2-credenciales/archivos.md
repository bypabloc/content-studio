# Spec 034, fase 2: archivos

## server/src/content_studio/

### Crear

- `server/src/content_studio/credentials.py` — lectura, escritura, borrado y formato del token (solo stdlib).
- `server/src/content_studio/api/routes/credentials.py` — `GET/PUT/DELETE /credentials/huggingface`.
- `server/tests/unit/src/content_studio/test_credentials.py` y `server/tests/unit/src/content_studio/api/routes/test_credentials.py`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio -q -k credentials`

### Modificar

- `server/src/content_studio/api/routes/settings.py` — 403 para `secret.*`.
- `server/src/content_studio/api/routes/engines.py` — `gated` en la lista; 409 sin token.
- `server/src/content_studio/api/app.py` — registra la ruta.
- `server/src/content_studio/messages/{es,en,pt}.json` — los errores de 02 §5.
- `client/src/shared/api/schema.d.ts` — se regenera desde OpenAPI.
  - Verify: `python -m devtools test-runner --type=i18n,typecheck`
