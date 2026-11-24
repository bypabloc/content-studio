# Spec 029, fase 2: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server y client

### Crear

- `server/src/content_studio/mcp_server/config.py` — fragmentos por cliente.
- `server/src/content_studio/api/routes/integrations.py` — `GET /integrations/mcp-config` y su línea en `create_app`.
- `client/src/features/settings/McpConfig.tsx` y su test.
- `docs/operations/mcp.md` — cómo conectar cada cliente, qué herramientas hay y qué no.

### Modificar

- `client/src/features/settings/IntegrationsPanel.tsx` (028).
- `server/src/content_studio/messages/{es,en,pt}.json`.
- `client/src/shared/api/schema.d.ts` — `gen:api`.
  - Verify: `bun run --cwd client test && python -m devtools test-runner --type=i18n`
