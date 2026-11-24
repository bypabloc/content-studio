# Spec 026, fase 3: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/engines/recipes/

### Modificar

- `acestep.json`, `heartmula.json`, `faster-whisper.json`, `vision.json`, `llama-cpp.json`, `gemma-4-e4b.json`, `qwen3.5-9b.json`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q`
- `server/tests/integration/test_venvs.py` — `LIBRARIES` si cambia un import.
- `server/src/content_studio/music/engines/*.py`, `llm/runtime.py` — solo lo que pida una API nueva.
