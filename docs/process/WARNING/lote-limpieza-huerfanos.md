# Lote 001-017: borradas las 49 carpetas huérfanas de content-studio-worktrees

- **Contexto**: `../content-studio-worktrees/` tenía 49 carpetas sin `.git` que `git worktree list` no reconoce. Eran restos de cierres y de corridas de pytest y test-runner (`pytest-of-pacg1/`, `tmp-012-*`, `_tmp`, `spec-007-i18n`, etc.). Tenían 4 859 enlaces, todos dentro de su propia carpeta (`pytest-current` y similares). Ninguno apuntaba al checkout principal ni a otro worktree.
- **Elegida**: desenlazar primero, uno a uno, con `rmdir` y `del` sin `/S` (solo quitan el enlace), y después borrar cada carpeta con `Remove-Item -Recurse -Force`. Se conserva `012-engines-storage`, que sí está registrado en git.
- **Descartadas**: dejarlas (ocupaban disco y mezclaban temporales con worktrees reales); borrar con `Remove-Item -Recurse` sin desenlazar (en Windows puede seguir enlaces de directorio).
- **Cómo revertir**: no es reversible, pero eran temporales: los datos eran fixtures de pytest, regenerables con `uv run pytest`.
- **Cómo comprobarla**: `git worktree list` muestra solo `012-engines-storage`, y `Get-ChildItem ...\content-studio-worktrees -Directory` devuelve solo esa carpeta.
- **Pendiente**: ninguno.
