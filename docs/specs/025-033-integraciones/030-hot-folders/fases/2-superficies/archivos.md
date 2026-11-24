# Spec 030, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server y client

### Crear

- `server/src/content_studio/api/routes/inbox.py` y su línea en `create_app`.
- `server/src/content_studio/cli/inbox.py` y su línea en `build_parser`.
- `client/src/features/settings/InboxFolders.tsx` y su test; los e2e.

### Modificar

- `server/src/content_studio/mcp_server/tools.py` — `studio_watch_folder`.
- `docs/operations/mcp.md` (029) — la herramienta nueva.
- `server/src/content_studio/messages/{es,en,pt}.json`; `client/src/shared/api/schema.d.ts` (`gen:api`).
  - Verify: `bun run --cwd client test && python -m devtools test-runner --type=i18n`
