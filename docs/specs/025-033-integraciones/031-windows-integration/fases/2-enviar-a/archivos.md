# Spec 031, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## Instalador y client

### Modificar

- `client/src-tauri/installer/nsis/hooks.nsh` — crea y borra los accesos directos.
- `client/src/app/external/parseExternal.ts` — acciones `--send`.
- `server/src/content_studio/messages/{es,en,pt}.json` — `sendto.*`.

### Crear

- `tests/e2e/app-check/031-sendto.check.ts`.
  - Verify: `python -m devtools app-check run --binary=<exe> --scenario=031-sendto`
