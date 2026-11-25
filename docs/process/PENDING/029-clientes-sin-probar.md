# 029: clientes MCP sin probar en la app

- **Qué**: ningún cliente se probó todavía de punta a punta con su fragmento. Jan y LM Studio no documentan la forma stdio
  (su fragmento lleva `mcpServers` sin verificar). VS Code deja `.vscode/mcp.json` como deprecado en su documentación.
  Cursor, Claude Desktop y AnythingLLM llevan la forma oficial, sin probar en la app.
- **Por qué**: se verificó la forma en la documentación, pero no se abrió cada aplicación con su configuración.
- **Quién decide**: agente, con el usuario en la verificación final.
- **Qué lo cierra**: en la verificación final (03 §2), Claude Code y Codex con una narración corta; los demás, cuando se
  pruebe su fragmento. Lo que no se pueda probar se quita de la tabla de `docs/operations/mcp.md`.
