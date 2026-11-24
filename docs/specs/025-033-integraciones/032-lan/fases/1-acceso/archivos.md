# Spec 032, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/lan/

### Crear

- `server/src/content_studio/lan/__init__.py`, `clients.py`, `pairing.py`, `cert.py`, `server.py`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/lan -q`
- Tests espejo y `server/tests/integration/test_lan.py`.

### Modificar

- `server/src/content_studio/db/schema.py` — migración de 02 §3.
- `server/src/content_studio/cli/serve.py` — arranca el listener si está activo.
- `server/pyproject.toml`, `uv.lock` — `cryptography`.
- `server/src/content_studio/messages/{es,en,pt}.json` — `error.pairing_*`.
  - Verify: `python -m devtools test-runner --type=i18n`
