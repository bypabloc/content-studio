# Spec 030, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/inbox/

### Crear

- `server/src/content_studio/inbox/__init__.py`, `store.py`, `inputs.py`, `scanner.py`, `receipts.py` — solo stdlib.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/inbox -q`
- Tests espejo y `server/tests/integration/test_inbox.py`.

### Modificar

- `server/src/content_studio/db/schema.py` — la migración de 02 §3.
- `server/src/content_studio/cli/serve.py` — el hilo de sondeo y el barrido inicial.
- `server/src/content_studio/messages/{es,en,pt}.json` — los códigos de error.
  - Verify: `python -m devtools test-runner --type=i18n`
