# Spec 031, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/

### Crear

- `client/src/app/external/parseExternal.ts`, `useExternalRequests.ts` y sus tests.
- `client/src-tauri/src/external.rs` — reenvío de `argv`.

### Modificar

- `client/src-tauri/Cargo.toml` — `tauri-plugin-deep-link` y `tauri-plugin-single-instance` exactos.
- `client/src-tauri/src/lib.rs` — los registra primero.
- `client/src-tauri/tauri.conf.json` — `plugins.deep-link`.
- Las secciones Narración, Música y Conversor — aceptan un estado inicial.
- `server/src/content_studio/messages/{es,en,pt}.json` — `deeplink.*`.
  - Verify: `python -m devtools test-runner --type=tauri-check && bun run --cwd client test`
