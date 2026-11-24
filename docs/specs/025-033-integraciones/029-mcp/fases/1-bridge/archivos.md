# Spec 029, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/mcp_server/

### Crear

- `server/src/content_studio/mcp_server/__init__.py`, `tools.py`, `bridge.py` — herramientas y bridge stdio.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/mcp_server -q`
- Tests espejo y `server/tests/integration/test_mcp_bridge.py` (cliente MCP en memoria del SDK).

### Modificar

- `server/pyproject.toml`, `uv.lock` — dependencia `mcp` (exacta como cota inferior).
- `server/src/content_studio/cli/main.py` — `mcp` en `build_parser`.
- `server/src/content_studio/messages/{es,en,pt}.json` — `error.input_not_found`, `error.gpu_waiting`.
  - Verify: `python -m devtools test-runner --type=i18n`

### Solo lectura

- `server/src/content_studio/runtime/instance.py` y `discovery.py` (028).
- `server/src/content_studio/api/routes/jobs.py` — `create_job` y `job_outputs`.
