# Lote 001-017: 9 carpetas huérfanas en `content-studio-worktrees/`

- **Qué**: quedan 9 carpetas en `../content-studio-worktrees/` que no son worktrees de git: `_tmp`, `012-red-green-20261121-142017-2894`, `tmp-012-full-gate-20261121`, `tmp-012-t6-check`, `tmp-012-t6-coverage`, `tmp-012-t6-hook-fix`, `tmp-012-t6-targeted`, `tmp-012-test-runner` y `015-convert-normalize-trim`. Las ocho primeras solo tienen `pytest-of-pacg1/` o `pytest-base/` con archivos de otra cuenta, y tienen ACL de administrador. La de 015 la retiene un proceso: `worktree close` la quitó de git el 2026-11-22 y no pudo borrarla.
- **Por qué falta**: la sesión no es administradora (`takeown`, `icacls` y `rd` fallan con «Acceso denegado») en las ocho; en la de 015, el proceso que la retiene sigue vivo.
- **Cuándo**: cuando el usuario lo pida; no bloquea nada (no están en git ni en el camino de ningún worktree activo). La de 015 se borra cuando se suelte el proceso.
- **Quién**: usuario, desde una terminal como administrador: `rd /s /q "D:\Users\pacg1\projects\bypabloc\content-studio-worktrees\<carpeta>"` para cada una.
