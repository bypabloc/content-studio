# Lote 001-017: limpieza de carpetas huérfanas de content-studio-worktrees (41 de 49 borradas)

- **Contexto**: `../content-studio-worktrees/` tenía 49 carpetas sin `.git` que `git worktree list` no reconoce. Eran restos de cierres y de corridas de pytest y test-runner. Tenían 4 859 enlaces, todos dentro de su propia carpeta (`pytest-current` y similares). Ninguno apuntaba al checkout principal ni a otro worktree. Al borrar, 41 se fueron del todo. 8 quedaron con archivos de `pytest-of-pacg1/` y `pytest-base/` con ACL de otra cuenta (creados en corridas elevadas): ni se pueden leer ni cambiar su propietario sin administrador.
- **Elegida**: desenlazar primero, uno a uno, con `rmdir` y `del` sin `/S` (solo quitan el enlace); después borrar archivo por archivo con `Remove-Item -Force`; y, por último, borrar cada carpeta. Las 8 bloqueadas se dejan tal cual y se anotan en PENDING. Se conserva `012-engines-storage`, que sí está registrado en git.
- **Descartadas**: forzar el propietario con `takeown` o `icacls` (falla sin administrador); borrar con `Remove-Item -Recurse` sin desenlazar (en Windows puede seguir enlaces de directorio).
- **Cómo revertir**: no es reversible, pero eran temporales: los datos eran fixtures de pytest, regenerables con `uv run pytest`.
- **Cómo comprobarla**: `git worktree list` muestra solo `012-engines-storage`. Las 8 bloqueadas están en PENDING con el comando de terminal elevada.
- **Pendiente**: [lote-huerfanos-bloqueadas](../PENDING/lote-huerfanos-bloqueadas.md).
