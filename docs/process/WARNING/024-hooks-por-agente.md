# 024: cómo bloquea Computer Use cada agente

- **Contexto**: `computer_use_guard.py` es compartido. Cada agente nombra distinto sus herramientas y tiene sus reglas para correr los hooks del proyecto.
- **Elegida**:
  - **Claude Code**: PreToolUse con matcher de las herramientas MCP de control del escritorio (`mcp__computer-use__*`, `mcp__remote-devices__computer*`). Exit 2 y el motivo en stderr.
  - **Codex** (CLI 0.171): Computer Use corre en `mcp__node_repl__js` con `@oai/sky`. En modo código, la llamada externa es `exec`, y según la documentación las llamadas anidadas también pasan por el hook. Se bloquea por contenido (`@oai/sky` o `sky.<método>(`) en `mcp__node_repl__js`, `js` y `exec`, con exit 2. Codex solo corre los hooks de un proyecto confiable y aprobados con `/hooks`. Un hook nuevo o cambiado queda pendiente hasta aprobarlo. Por eso `~/.codex/config.toml` hoy solo tiene aprobados los de engram, y `shell_guard.py` tampoco corría en Codex.
  - **Antigravity**: `.agents/hooks.json`, con `{"decision": "deny"}` en stdout. Su documentación no lista una herramienta de control del escritorio, solo de navegador (`browser_.*`). El matcher toma cualquier herramienta con `computer` en el nombre, para que el agente tenga la misma regla que los otros dos.
- **Descartadas**: `[features] computer_use = false` (esa clave no existe en la configuración de Codex) y `[plugins."computer-use@openai-bundled"] enabled = false` en el `.codex/config.toml` del proyecto (la documentación no cubre el marketplace `openai-bundled` y un refresh puede reinstalarlo; sin prueba, sería configuración que no se sabe si actúa). El sondeo con `--dangerously-bypass-hook-trust` lo bloqueó Synapse, con razón.
- **Cómo revertir**: quitar las entradas de `computer_use_guard.py` de `.claude/settings.json`, `.codex/hooks.json` y `.agents/hooks.json`.
- **Cómo comprobarla**: `uv run pytest .agents/hooks`. En Codex, aprobar los hooks con `/hooks` y pedir `sky.list_apps()`: debe responder con el mensaje de `computer_use_guard.py`.
- **Pendiente**: [024-aprobar-hooks-codex](../PENDING/024-aprobar-hooks-codex.md).
