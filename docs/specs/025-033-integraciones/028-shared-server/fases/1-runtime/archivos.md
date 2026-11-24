# Spec 028, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/runtime/

### Crear

- `server/src/content_studio/runtime/__init__.py`, `discovery.py`, `instance.py`, `idle.py` — solo stdlib.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/runtime -q`
- `server/src/content_studio/cli/api.py` — `up`, `status`, `down`, `token`.
- Tests espejo en `server/tests/unit/src/content_studio/runtime/` y `cli/test_api.py`; `server/tests/integration/test_shared_server.py`.

### Modificar

- `server/src/content_studio/cli/main.py` — una línea en `build_parser`.
- `server/src/content_studio/cli/serve.py` — puerto, lock, `api.json` y el hilo de inactividad.
- `server/src/content_studio/api/app.py` — middleware de actividad y de Host.
- `server/src/content_studio/api/routes/health.py` — `version` y `pid`.
- `server/src/content_studio/messages/{es,en,pt}.json` — `error.host_not_allowed`.
  - Verify: `python -m devtools test-runner --type=i18n`
