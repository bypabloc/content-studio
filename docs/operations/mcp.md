# Servidor MCP de content-studio (`studio mcp`)

Un asistente (Claude Code, Codex, VS Code, Cursor, Claude Desktop, LM Studio, Jan o AnythingLLM) puede pedir narraciones,
música, transcripciones, limpiezas de silencios y conversiones, esperar el resultado y recibir la ruta del archivo.
El servidor habla MCP por stdio y pasa los trabajos por el server compartido de la app, que arranca solo si hace falta.

## Configurar un cliente

- En la app: Ajustes > Integraciones > «Conectar un asistente (MCP)». Eliges la aplicación y copias la configuración.
- En la terminal: `studio mcp config --client <cliente>` imprime el fragmento (JSON o TOML).

| Cliente (`--client`) | Archivo | Clave | Estado |
| :--- | :--- | :--- | :--- |
| `claude-code` | `.mcp.json` del proyecto | `mcpServers` | Forma de la documentación oficial |
| `codex` | `%USERPROFILE%\.codex\config.toml` | `[mcp_servers.content-studio]` | Forma de la documentación oficial |
| `vscode` | `.vscode\mcp.json` del workspace | `servers`, con `"type": "stdio"` | Forma oficial; el archivo queda deprecado en la documentación |
| `cursor` | `.cursor\mcp.json` | `mcpServers` | Forma oficial, sin probar en la app |
| `claude-desktop` | `%APPDATA%\Claude\claude_desktop_config.json` | `mcpServers` | Forma oficial, sin probar en la app |
| `lm-studio` | `mcp.json` (Settings > Program > Edit mcp.json) | `mcpServers` | Forma stdio no documentada: no verificado |
| `jan` | no documentada | `mcpServers` | No verificado |
| `anythingllm` | `storage\plugins\anythingllm_mcp_servers.json` | `mcpServers` | Forma oficial, sin probar en la app |

Lo que no se probó de verdad está en [PENDING/029-clientes-sin-probar](../process/PENDING/029-clientes-sin-probar.md).

El comando que el cliente lanza es el `studio` de la instalación (`studio.exe mcp`); en un checkout, `uv run --project server studio mcp`.

## Herramientas

| Herramienta | Para qué |
| :--- | :--- |
| `studio_capabilities` | Motores instalados, voces, estilos y tipos de trabajo |
| `studio_narrate` | Narrar un texto o un guion con una voz |
| `studio_make_music` | Música de fondo instrumental |
| `studio_transcribe` | Transcribir audio o video |
| `studio_clean_silences` | Analizar silencios para proponer cortes |
| `studio_convert_media` | Convertir a otro formato o a un preset |
| `studio_submit_job` | Encolar cualquier tipo de trabajo con sus `params` |
| `studio_get_job` | Estado de un trabajo, o de los últimos 10 |
| `studio_wait_job` | Esperar hasta 300 s, con progreso; devuelve las rutas de salida |
| `studio_cancel_job` | Cancelar un trabajo; su proceso termina |

Cada salida llega como ruta y como `resource_link` `file:///`; nunca como base64. Un trabajo de GPU que espera a otra
sesión muestra `waiting_gpu` y dice quién tiene la GPU.

## Qué no expone

Instalar o desinstalar motores, mover almacenamiento, ajustes, el explorador de archivos (`/fs`), la papelera y borrar
ítems de la biblioteca. Un guion o un subtítulo puede traer instrucciones escritas para el asistente, así que no hay
herramientas administrativas a las que esas instrucciones puedan llegar.

## Entradas

Cualquier archivo existente de este equipo. Una ruta que no existe responde `input_not_found` y no encola nada.
