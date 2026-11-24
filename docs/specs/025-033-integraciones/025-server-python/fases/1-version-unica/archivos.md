# Spec 025, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## Raíz

### Crear

- `.python-version` — la versión elegida (D-1).
  - Verify: `uv run python --version`
- `tests/validators/test_python_version.py` — AC-1 y AC-2.
  - Verify: `uv run pytest tests/validators/test_python_version.py -q`
- `devtools/python_floor.py` — `engine_floor() -> tuple[int, int]` desde las recetas.
  - Verify: `uv run pytest devtools/tests/unit/test_python_floor.py -q`
- `devtools/tests/unit/test_python_floor.py` — espejo del módulo.

### Modificar

- `server/pyproject.toml` — `requires-python`.
- `pyproject.toml` — comentarios de ruff `target-version` y mypy `python_version` (quedan en el piso, 3.10 hoy).
- `.github/workflows/calidad.yml` — una versión, desde `.python-version` (D-3).
- `tests/validators/test_structure.py` — el piso sale de `engine_floor()`.
  - Verify: `uv run pytest tests/validators -q`

### Solo lectura

- `server/src/content_studio/common/process.py` — `use_venv` y `env_src`, por qué existe el piso.
- `server/src/content_studio/engines/recipes/*.json` — el paso `python`.
