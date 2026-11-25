---
modulo: integraciones
actualizada: 2026-11-25
---

# Integraciones

## Qué resuelve

Conecta asistentes y agentes locales (Claude Code, Codex, VS Code, Cursor, Claude Desktop, LM Studio, Jan y AnythingLLM)
con content-studio: piden una narración o una música, esperan el resultado y reciben la ruta del archivo, sin abrir la app.

## Qué hace hoy

- `studio mcp`: servidor MCP por stdio con diez herramientas `studio_*`: capacidades, narrar, música, transcribir,
  limpiar silencios, convertir, y la cola (enviar, consultar, esperar y cancelar). Lista cerrada, sin administración.
- Las salidas llegan como ruta y como `resource_link` `file:///`. `studio_wait_job` emite progreso y, si vence, devuelve
  el estado sin error.
- Un trabajo de GPU que espera a otra sesión muestra `waiting_gpu` y dice quién tiene la GPU.
- Ajustes > Integraciones > «Conectar un asistente (MCP)»: eliges la aplicación y copias su configuración. `studio mcp
  config --client <c>` imprime lo mismo en la terminal.
- Formatos de cada cliente, lo que no se probó y las herramientas: `docs/operations/mcp.md`.

## Dónde vive

- `server/src/content_studio/mcp_server/` (catálogo, herramientas, puente, SDK y configuración por cliente),
  `cli/mcp.py` y `api/routes/integrations.py`.
- Cliente: `client/src/features/settings/McpConfig.tsx`, dentro de `IntegrationsPanel.tsx`.

## Historial

- 2026-11-25: spec 029: servidor MCP por stdio y configuración por cliente.
