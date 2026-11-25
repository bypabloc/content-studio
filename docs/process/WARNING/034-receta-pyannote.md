# 034: receta de pyannote en Python 3.14, no 3.12

- **Contexto**: la spec 034 fijaba Python 3.12 (D-5). La 026 (PR #109) llevó cada receta a la Python más alta que soporta: `recipes.PYTHON` admite de 3.10 a 3.15 y `qwen-0.6b` usa 3.14 con torch 2.11.0+cu128. Sin ajustar, la receta de pyannote quedaría fuera de esa política.
- **Elegida**: Python 3.14, con torch y torchaudio `2.11.0+cu128`, pyannote.audio `4.1.1`, torchcodec `0.17.0` y huggingface-hub `0.36.2`. Comprobado con `uv pip compile --python-version 3.14 --python-platform x86_64-pc-windows-msvc --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cu128`: resuelve sin errores (`logs/preflight-034-pyannote-314.log`). Comparte índice y stack con Qwen.
- **Descartadas**: 3.12 (contradice la política de la 026 y obligaría a un venv aparte sin motivo); 3.15 (cu128 no tiene ruedas cp315 según `NOTES.md` del lote; cu130 sí, pero trae otro índice y otra versión de torch que Qwen no usa).
- **Cómo revertir**: volver a `"version": "3.12"` en `server/src/content_studio/engines/recipes/pyannote.json` y en la spec (D-5).
- **Cómo comprobarla**: el comando de `uv pip compile` de arriba sin errores, y `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q` tras la fase 1.
- **Pendiente**: ninguno en esta ficha; la instalación real queda en la verificación final de la 034.
