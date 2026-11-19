# 005: el node_modules del principal recibió dependencias del worktree

- **Qué**: antes del fix de `prepare` (WARNING 005-worktree-prepare), el `node_modules` del checkout principal recibió el store `.bun` de las dependencias del worktree 005-client-base (295 entradas). Es regenerable y no toca git.
- **Por qué no se hizo**: el checkout principal no se toca durante un lote (regla de `agentes-y-tokens.md`).
- **Cuándo**: después del lote, cuando el usuario quiera.
- **Quién**: usuario o agente fuera del lote.
- **Qué la cierra**: `bun install --frozen-lockfile` en el principal (con su `bun.lock` de dev) sin errores, y `git status` del principal limpio.
