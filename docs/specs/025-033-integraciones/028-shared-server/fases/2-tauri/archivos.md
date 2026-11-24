# Spec 028, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/src-tauri/

### Modificar

- `client/src-tauri/src/lib.rs` — `connect` con `api up`; sin Job para el server.
- `client/src-tauri/src/server.rs` — `parse_ready` con `url` y `token`; `job::KillOnClose` queda solo si algo más lo usa.
- El hook del updater (`shared/update/useUpdater.ts` o el lado Rust) — `api down --force` antes de instalar.
  - Verify: `python -m devtools test-runner --type=tauri-check`
