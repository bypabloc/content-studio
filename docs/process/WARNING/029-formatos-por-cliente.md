# 029: la forma de cada archivo MCP sale de la documentación oficial

- **Contexto**: 02 §3 pide el fragmento de ocho clientes. Una verificación con la documentación oficial (2026-11-25) dio la
  clave y la forma de cada archivo; Jan y LM Studio no documentan la forma stdio.
- **Elegida**: `mcpServers` para Claude Code, Cursor, Claude Desktop, LM Studio, Jan y AnythingLLM; `servers` con
  `"type": "stdio"` para VS Code; TOML `[mcp_servers.content-studio]` para Codex. Jan y LM Studio llevan la forma
  `mcpServers` sin verificar (ficha PENDING `029-clientes-sin-probar`).
- **Descartadas**: HTTP (`url`) en el fragmento: el HTTP llega con la LAN (032); instrucciones de copia a mano sin fragmento.
- **Cómo revertir**: cambiar `fragment()` en `server/src/content_studio/mcp_server/config.py`.
- **Cómo comprobarla**: `uv run studio mcp config --client <cliente>` y `test_config.py`.
- **Pendiente**: [PENDING/029-clientes-sin-probar](../PENDING/029-clientes-sin-probar.md).
