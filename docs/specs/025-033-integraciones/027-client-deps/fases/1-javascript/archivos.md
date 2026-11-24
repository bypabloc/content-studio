# Spec 027, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## JavaScript

### Modificar

- `client/package.json`, `tests/e2e/package.json`, `package.json`, `bun.lock` — versiones nuevas exactas.
  - Verify: `bun install --frozen-lockfile`
- `client/src/**` — lo que pida una API nueva.
  - Verify: `bun run --cwd client typecheck && bun run --cwd client lint && bun run --cwd client test`
- `docs/process/WARNING/005-typescript-5.md` — se actualiza o se borra con su fila (D-2).

### Crear

- `tests/validators/test_pins.py` — sin rangos en los manifiestos.
