# Lote 001-017: 8 carpetas huérfanas bloqueadas por ACL de administrador

- **Qué**: quedan 8 carpetas en `../content-studio-worktrees/` que no son worktrees de git: `_tmp`, `012-red-green-20261121-142017-2894`, `tmp-012-full-gate-20261121`, `tmp-012-t6-check`, `tmp-012-t6-coverage`, `tmp-012-t6-hook-fix`, `tmp-012-t6-targeted` y `tmp-012-test-runner`. Solo tienen `pytest-of-pacg1/` o `pytest-base/` con archivos de otra cuenta.
- **Por qué falta**: la sesión no es administradora; `takeown`, `icacls` y `rd` fallan con «Acceso denegado».
- **Cuándo**: cuando el usuario lo pida; no bloquea nada (no están en git ni en el camino de ningún worktree activo).
- **Quién**: usuario, desde una terminal como administrador: `rd /s /q "D:\Users\pacg1\projects\bypabloc\content-studio-worktrees\<carpeta>"` para cada una.
