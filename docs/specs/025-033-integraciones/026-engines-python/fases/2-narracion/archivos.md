# Spec 026, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/engines/recipes/

### Modificar

- `voxcpm2.json`, `qwen-0.6b.json`, `qwen-1.7b.json`, `chatterbox.json`, `cosyvoice3.json`, `omnivoice.json`, `indextts.json` — Python, torch, paquetes, commit y revisión.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q`
- `server/src/content_studio/narration/engines/*.py` — solo lo que cambie la API de una librería nueva.

### Crear

- `docs/process/WARNING/026-<motor>-version.md` y `PENDING/026-reintentar-<motor>.md`, por motor que quede por debajo.
