# 025: la CI corre una sola versión de Python (la de .python-version)

- **Contexto**: `calidad.yml` tenía una matriz 3.10 y 3.12. Con `requires-python` en 3.15, `uv sync` no puede crear un venv 3.10 con fastapi, y el piso de sintaxis de los motores lo valida ya `test_structure.py` con `engine_floor()` (D-2).
- **Elegida**: `uv sync --group dev` sin matriz; uv toma la versión de `.python-version` (3.15). Una sola versión (D-3).
- **Descartadas**: mantener 3.10 en la matriz (obligaría a dejar `requires-python` en 3.10 y no deja usar la sintaxis nueva del server); matriz 3.15 + 3.12 (el server y el instalador van en 3.15 por D-1, probar otra versión no aporta).
- **Cómo revertir**: restaurar la `strategy.matrix` de `.github/workflows/calidad.yml` y `requires-python` anterior, en el commit de la fase 1.
- **Cómo comprobarla**: `uv run pytest tests/validators/test_python_version.py` (AC-2) y `python -m devtools test-runner --type=all` en 3.15. Nota: `git-workflow.md` dice que `calidad.yml` no corre en los PR de bypabloc: la prueba real es la local.
- **Pendiente**: ninguno.
