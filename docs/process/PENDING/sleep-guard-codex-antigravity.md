# sleep-guard: comprobar que el hook bloquea en Codex y Antigravity

- **Qué**: `.agents/hooks/sleep_guard.py` está conectado en `.codex/hooks.json` (PreToolUse de `^Bash$`, bloquea con exit 2) y en `.agents/hooks.json` (PreToolUse de `run_command`, responde `{"decision": "deny"}` en stdout). En Claude Code está probado; en Codex y Antigravity no se ejecutó.
- **Por qué no se hizo**: no hay Codex ni Antigravity en este equipo. La documentación de Antigravity ([antigravity.google/docs/hooks](https://antigravity.google/docs/hooks)) no trae un ejemplo literal de `deny` en PreToolUse ni documenta exit codes; hay reportes de que PreToolUse no dispara en el IDE 2.0 y en Windows. Codex pide aprobar hooks nuevos en `/hooks` ([learn.chatgpt.com/docs/hooks](https://learn.chatgpt.com/docs/hooks)).
- **Cuándo**: la próxima vez que se use Codex o Antigravity en este repo.
- **Quién**: usuario (o el agente desde esa herramienta).
- **Qué la cierra**: en cada herramienta, pedirle que corra `sleep 5` en primer plano y ver que lo rechaza con el motivo de `sleep_guard.py`; si Antigravity no lo bloquea, ajustar la salida del script al formato real.
