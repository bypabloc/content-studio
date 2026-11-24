# Spec 029: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `029-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-029/` o `tmp/spec-029/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run studio <comando> --help`, un caso real y uno de error; sin TTY (`| cat`) no pregunta nada | toca el CLI |
| 4 | `python -m devtools test-runner --type=e2e` | toca el client |
| 5 | `python -m devtools app-check run` | toca la UI o el arranque de la app |
| 6 | `npx @modelcontextprotocol/inspector uv run studio mcp` (lista y llama herramientas) | siempre |
| 7 | Duración y LUFS de la narración pedida por el agente contra la de `studio narration tts` | siempre (AC-11) |

## 2. Comprobaciones propias

1. Claude Code: `claude mcp add` con el fragmento de `studio mcp config --client claude-code`; pedir una narración corta y una música de 30 s; las rutas existen [AC-11].
2. Codex CLI con su TOML; misma prueba [AC-11].
3. LM Studio con Qwen3.5 9B si está instalado: pedir una conversión a MP3; si no, ficha en `PENDING/029-clientes-sin-probar.md`.
4. Con otra sesión ocupando la GPU (`gpu-turn run --job=prueba -- …`), `studio_get_job` dice `waiting_gpu` [AC-7].

## 3. Escucha

La narración que pidió el agente va en el PR junto a la de `studio narration tts` para comparar.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `server.md` (MCP) y una ficha nueva `integrations.md` («Qué resuelve», «Qué hace hoy», «Dónde vive»).
- [ ] Reglas y docs actualizadas: `AGENTS.md` (tabla de herramientas: `studio mcp`), `stack.md` §1 (SDK `mcp`) y `codigo-python.md` (cómo agregar una herramienta MCP); `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head feature/029-mcp`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales), rutas de `out/` y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 029-mcp`.
