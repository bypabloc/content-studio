# 029: el protocolo MCP usa el SDK oficial `mcp` 2.3.0

- **Contexto**: `studio mcp` debe hablar MCP por stdio con Claude Code, Codex y los demás clientes. El SDK oficial trae
  la inicialización, el progreso y la cancelación (D-1 de la spec 029).
- **Elegida**: `mcp>=2.3.0` en `server/pyproject.toml` (la versión instalada al implementar). Se importa solo dentro de
  `mcp_server/sdk.py` y `cli/mcp.py`: `studio` sin el paquete arranca igual, y `studio mcp` sale con 2 y lo dice.
- **Descartadas**: escribir el JSON-RPC a mano (más código que mantener, sin ganancia).
- **Cómo revertir**: quitar la línea de `server/pyproject.toml`, volver `uv.lock` a `origin/dev` y borrar `sdk.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/integration/test_mcp_bridge.py::test_ac1_protocolo_lista_las_diez_herramientas`.
