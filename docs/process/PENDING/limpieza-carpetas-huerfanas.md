# Carpetas huérfanas en content-studio-worktrees

- **Qué**: `../content-studio-worktrees/` tiene más de 150 carpetas que no son worktrees registrados (`p019-*`, `pytest-0*`, `pytest018*`, `tmp-012-*`, `_tmp`, `tmp` y cierres viejos como `013-whisper-cleaner`). Son restos de corridas de pytest y de cierres. Algunas tienen ACL de administrador.
- **Por qué no se hizo**: Synapse bloquea borrar fuera del proyecto y pide aprobación manual. Además, `retained/` guarda salidas para escuchar.
- **Cuándo**: cuando quieras liberar espacio; no bloquea nada.
- **Quién**: usuario (aprueba en Synapse o borra desde una terminal de administrador).
- **Qué la cierra**: dejar solo los worktrees de `git worktree list` y `retained/`. No borrar `017-editor-core` ni `ignorar-chequeos-voz`, que siguen registrados.
