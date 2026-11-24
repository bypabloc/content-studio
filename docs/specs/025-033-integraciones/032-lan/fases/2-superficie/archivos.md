# Spec 032, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/

### Crear

- `server/src/content_studio/lan/guard.py` — `REMOTE_KINDS` y la guarda de parámetros.
- `server/src/content_studio/api/routes/uploads.py`.

### Modificar

- `server/src/content_studio/api/app.py` — `remote=True`.
- `server/src/content_studio/mcp_server/bridge.py` — la variante HTTP.
- `server/src/content_studio/messages/{es,en,pt}.json` — `error.remote_path_not_allowed`, `kind_not_allowed_remote`, `upload_too_large`.
  - Verify: `uv run pytest server/tests -q && python -m devtools test-runner --type=i18n`
