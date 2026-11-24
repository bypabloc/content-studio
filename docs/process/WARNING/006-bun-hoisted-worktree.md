# 006: el worktree instala con el enlazador hoisted (límite de rutas de Windows)

- **Contexto**: en esta máquina `LongPathsEnabled` está en 0. Con el enlazador por defecto, bun guarda los paquetes en `node_modules/.bun/…`, y dos de ellos (`@tanstack/react-query` y `@redocly/openapi-core`) llegan a 255 caracteres al copiarse en un worktree con nombre largo (`006-narration-section`). `bun install` falla con `ENOENT … (copyfile)`. La 005 (nombre de 15 caracteres) no llegaba a ese límite.
- **Elegida**: `worktree prepare` corre `bun install --frozen-lockfile --linker hoisted` (`devtools/worktree.py`, `_bun_install`). El principal sigue con el enlazador por defecto. El lockfile no cambia: son las mismas versiones, en otra disposición en disco.
- **Descartadas**: activar `LongPathsEnabled` (cambio de sistema que pide administrador); acortar el nombre del worktree (solo aplaza el problema a la siguiente spec); mapear una unidad con `subst`.
- **Cómo revertir**: quitar `--linker hoisted` de `_bun_install` cuando `LongPathsEnabled` esté en 1 en la máquina de desarrollo.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_worktree.py -k hoisted`, y `python -m devtools worktree prepare <nombre>` en un worktree de nombre largo: `bun install` termina sin `failed to link package`.
- **Antes de**: el merge a `dev` de la 006.
