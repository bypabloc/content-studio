# Lote 001-017: 10 carpetas huérfanas en `content-studio-worktrees/`

- **Qué**: quedan 10 carpetas que no son worktrees de git: `_tmp`, `012-red-green-20261121-142017-2894`, `tmp-012-full-gate-20261121`, `tmp-012-t6-check`, `tmp-012-t6-coverage`, `tmp-012-t6-hook-fix`, `tmp-012-t6-targeted`, `tmp-012-test-runner`, `015-convert-normalize-trim` y `016-mix-ducking`.
- **Por qué falta**: las ocho carpetas de pytest tienen ACL de administrador; un proceso retiene la de 015; Synapse exige aprobación manual para borrar recursivamente la de 016 fuera de `tmp`.
- **Cuándo**: cuando el usuario lo autorice en su terminal; no bloquea las specs del lote.
- **Quién**: usuario.
- **Qué la cierra**: borrar las carpetas huérfanas; no tocar datos de usuario ni worktrees registrados.
