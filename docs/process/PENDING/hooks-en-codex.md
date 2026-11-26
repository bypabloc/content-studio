# Aprobar y probar los hooks del proyecto en Codex y Antigravity

- **Qué**: `.agents/hooks/shell_guard.py` (sleep, wsl, `--no-verify`) y `computer_use_guard.py` están conectados en `.codex/hooks.json` y `.agents/hooks.json`, pero solo se probaron en Claude Code. Codex pide aprobar cada hook nuevo en `/hooks`.
- **Por qué no se hizo**: la aprobación es interactiva y la guarda Codex en la configuración del usuario.
- **Cuándo**: la próxima vez que uses Codex o Antigravity en este repo, y otra vez cada vez que cambie un hook.
- **Quién**: usuario.
- **Qué la cierra**: en Codex, aprobar los dos hooks en `/hooks`. Después, pedirle `sleep 5` y `wsl -l` y ver que los rechaza con el motivo del hook. En Antigravity, la misma prueba; si no bloquea, el agente ajusta la salida del script.
