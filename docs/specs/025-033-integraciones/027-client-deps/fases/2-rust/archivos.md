# Spec 027, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/src-tauri/

### Modificar

- `client/src-tauri/Cargo.toml`, `Cargo.lock` — versiones y edición.
- `client/src-tauri/src/**` — lo que cambie de API.
  - Verify: `python -m devtools test-runner --type=tauri-check`
