# 026: pyannote en Python 3.14, por debajo de .python-version (3.15)

- **Contexto**: `test_ac1_every_engine_below_pinned_python_has_warning` exige una ficha `026-<motor>-version.md` para cada receta con Python menor que `.python-version`. La receta de pyannote va en 3.14 (fase 0-ajustes de la 034, `WARNING/034-receta-pyannote`).
- **Elegida**: 3.14, porque cu128 no tiene ruedas de torch para cp315 (`NOTES.md` del lote). Es el mismo stack que `qwen-0.6b`.
- **Descartadas**: 3.15 con cu130 (otro índice y torch 2.14.x, distinto del de Qwen).
- **Cómo revertir**: cuando haya torch cu128 para cp315, subir la receta a 3.15 y borrar esta ficha.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q`.
- **Pendiente**: ninguno.
