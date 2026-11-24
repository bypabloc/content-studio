# Spec 026, fase 4: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## Raíz

### Modificar

- `pyproject.toml` — ruff `target-version` y mypy `python_version`.
- Los `.py` que `ruff check --fix` reescriba con las reglas `UP`.
  - Verify: `uv run ruff check && uv run ruff format --check && uv run pytest -q`
