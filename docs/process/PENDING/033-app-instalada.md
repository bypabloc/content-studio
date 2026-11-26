# 033: Recorrer la verificación integral sobre la app instalada: instalador, enlaces, «Enviar a» y MCP con la app cerrada

- **Qué**: 03 §7 de la 033, pasos 2, 3 y 5 con el binario instalado: `devtools bundle`, `tauri build`, `app-check run --binary=<instalador> --scenario=installed --scenario=031-sendto`, `content-studio://new/narration?text=Hola` (prellena sin encolar) y «Enviar a» con dos archivos (encola dos). Claude Code con `studio mcp` de la instalación y la app cerrada.
- **Por qué no se hizo**: instalar encima de la instalación del usuario cambia sus datos y su versión (`WARNING/025-instalador-real`), y eso lo decide el usuario. Lo mismo se probó desde el checkout: el MCP por stdio narró (VoxCPM2, 4,94 s, −16,0 LUFS) e hizo música de 30 s (ACE-Step, 30,00 s, −16,8 LUFS). Una carpeta de entrada convirtió un WAV con ffmpeg real. Con `api.idle_minutes` = 1 el server se apagó a los 95 s y una llamada MCP lo levantó con otro pid. Las cuatro puertas en un solo server las prueba `test_integrations_together.py`.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: usuario (instalar) y agente (`app-check --binary`).
- **Qué la cierra**: `app-check` con `--binary` en verde y los pasos 3 y 5 hechos con la app instalada.
