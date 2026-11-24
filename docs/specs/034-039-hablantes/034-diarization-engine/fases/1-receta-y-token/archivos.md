# Spec 034, fase 1: archivos

## server/src/content_studio/engines/

### Crear

- `server/src/content_studio/engines/recipes/pyannote.json` — receta (02 §3).
  - Verify: `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q`

### Modificar

- `server/src/content_studio/engines/recipes.py` — `diarization`, `gated` y `Recipe.gated`.
- `server/src/content_studio/engines/steps.py` — `HF_TOKEN` solo en pasos restringidos; exit 25.
- `server/src/content_studio/engines/installer.py` — `EXIT_CODES['engine_gated']`; lee el token si la receta es restringida.
- `server/tests/unit/src/content_studio/engines/test_recipes.py`, `test_steps.py` y `test_installer.py`.
- `server/tests/integration/test_venvs.py` — `LIBRARIES['pyannote'] = 'pyannote.audio'`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`

### Solo lectura

- `server/src/content_studio/engines/recipes/qwen-0.6b.json` — patrón de torch con cu128.
- `server/src/content_studio/engines/recipes/vision.json` — paso `hf` con `allow_patterns`.
