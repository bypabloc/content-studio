---
modulo: integraciones
actualizada: 2026-11-25
---

# Integraciones

## Qué resuelve

Conecta asistentes y agentes locales (Claude Code, Codex, VS Code, Cursor, Claude Desktop, LM Studio, Jan y AnythingLLM)
con content-studio: piden una narración o una música, esperan el resultado y reciben la ruta del archivo, sin abrir la app.

## Qué hace hoy

- `studio mcp`: servidor MCP por stdio con once herramientas `studio_*`: capacidades, narrar, música, transcribir,
  limpiar silencios, convertir, y la cola (enviar, consultar, esperar y cancelar), y `studio_watch_folder` (registrar una carpeta de entrada). Lista
  cerrada, sin administración.
- Las salidas llegan como ruta y como `resource_link` `file:///`. `studio_wait_job` emite progreso y, si vence, devuelve
  el estado sin error.
- Un trabajo de GPU que espera a otra sesión muestra `waiting_gpu` y dice quién tiene la GPU.
- Ajustes > Integraciones > «Conectar un asistente (MCP)»: eliges la aplicación y copias su configuración. `studio mcp
  config --client <c>` imprime lo mismo en la terminal.
- Formatos de cada cliente, lo que no se probó y las herramientas: `docs/operations/mcp.md`.
- Carpetas de entrada (spec 030): `studio inbox add|list|remove` y Ajustes > Integraciones > «Carpetas de entrada».
  Lo que se suelta en una carpeta se procesa solo; el resultado queda en su `done/` (o `failed/`), con un recibo JSON.
  Un archivo se toma cuando su tamaño y su fecha no cambian entre dos sondeos (cada 2 s). `keep_awake` mantiene el
  server encendido mientras la carpeta esté activa.

- Enlaces `content-studio://` (spec 031): `open/<sección>`, `job/<id>`, `library/<id>` y `new/<tipo>` abren o prellenan una sección, y con la app abierta el enlace llega a su ventana. Nunca encolan: el usuario pulsa el botón de la sección.
- «Enviar a» del Explorador (spec 031): «Convertir a MP3», «Normalizar», «Limpiar silencios» y «Transcribir» encolan un trabajo por archivo y avisan cuántos entraron y cuántos se saltaron; «Abrir en el Editor» abre los archivos en el Editor.
- Inicio con Windows (spec 031): Ajustes > Sistema > «Iniciar el servidor con Windows» escribe el valor `Run` de HKCU, apagado por defecto.
- Red local (spec 032), apagada por defecto: Ajustes > Integraciones > Red local abre un segundo listener con TLS en la IP elegida (`:41831`) y la regla de firewall «Content Studio LAN» solo para redes privadas (pide UAC). Un dispositivo se empareja con un PIN de 6 dígitos (5 min, un uso, 5 intentos) y recibe su token, que se puede revocar. Desde la LAN solo sube archivos (`upload:<id>`), pide narración, música, conversión, normalización o análisis de silencios, ve sus trabajos y baja sus salidas; también por MCP en `/mcp` (Streamable HTTP). Guía: `docs/operations/lan.md`.

## Dónde vive

- `server/src/content_studio/mcp_server/` (catálogo, herramientas, puente, SDK y configuración por cliente),
  `cli/mcp.py` y `api/routes/integrations.py`.
- Cliente: `client/src/features/settings/McpConfig.tsx`, dentro de `IntegrationsPanel.tsx`.
- Red local: `server/src/content_studio/lan/` (dispositivos, PIN, certificado, guarda, listener y MCP por HTTP), `api/routes/{remote,uploads,lan}.py`, `client/src-tauri/src/firewall.rs` y `client/src/features/settings/LanPanel.tsx`.

## Historial

- 2026-11-25: spec 029: servidor MCP por stdio y configuración por cliente.
- 2026-11-25: enlaces `content-studio://`, «Enviar a» e inicio con Windows (spec 031)
- 2026-11-25: red local con emparejamiento por PIN, TLS, subidas y MCP por HTTP (spec 032)
- 2026-11-25: verificación integral del lote 025-032 (spec 033): las cuatro puertas en un server; el server lanzado desde `studio mcp` pide salir del Job Object del cliente
