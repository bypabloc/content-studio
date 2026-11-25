# 029: clientes MCP sin probar dentro de su aplicación

- **Qué**: la verificación real del server (stdio con el SDK y el inspector oficial, narración real, turno de GPU) pasó.
  Falta probar el fragmento dentro de cada aplicación:
  - Claude Code y Codex CLI (AC-11): añadir el fragmento de `studio mcp config --client claude-code` o `codex`, pedir
    «narra este texto con la voz <v>» y comprobar que el archivo aparece en `out/narration/` y que el agente devuelve su ruta.
  - LM Studio, Jan, VS Code, Cursor, Claude Desktop y AnythingLLM: sin probar en la app. Jan y LM Studio no documentan la
    forma stdio, así que su fragmento lleva `mcpServers` sin verificar. VS Code deja `.vscode/mcp.json` como deprecado.
- **Por qué**: no se abrió ninguna de estas aplicaciones con su configuración en este equipo.
- **Quién decide**: agente, con el usuario para el gusto de la narración (AC-11 pide su escucha).
- **Qué lo cierra**: la prueba de cada cliente arriba. Lo que no se pueda probar se quita de la tabla de `docs/operations/mcp.md`.
