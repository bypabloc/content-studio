# Spec 031, fase 3: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/

### Crear

- `client/src-tauri/src/startup.rs` — escribir y borrar el valor.

### Modificar

- `client/src-tauri/Cargo.toml` — feature `Win32_System_Registry` de `windows`.
- `client/src/features/settings/` — el interruptor.
- `server/src/content_studio/messages/{es,en,pt}.json` — `settings.system.*`.
  - Verify: `python -m devtools test-runner --type=tauri-check && bun run --cwd client test`
