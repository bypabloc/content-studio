# Spec 025, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## Raíz y server

### Modificar

- `pyproject.toml`, `server/pyproject.toml` — cotas inferiores iguales al lock (D-4).
- `uv.lock` — `uv lock --upgrade`.
  - Verify: `uv lock --check`
- Lo que rompa una versión nueva en `server/src/` o `devtools/` (se lista en el commit).
  - Verify: `uv run pytest -q`

### Modificar (si aplica)

- `docs/process/PENDING/004-httpx-deprecado.md` y su fila — se borran si quedó resuelto.
