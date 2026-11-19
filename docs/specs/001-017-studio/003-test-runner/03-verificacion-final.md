# 003: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Batería

1. `python -m devtools test-runner --type=all`, con todo en `pass` y una línea JSON por etapa (AC-8).
2. `python -m devtools test-runner --type=guard-tdd` (AC-7).
3. `uv run pytest -q --co | tail -1`, igual a la base anotada (AC-9).
4. `uv run pytest -m local`: los tests `local` siguen funcionando después del movimiento a `integration/`.
5. `python -m devtools test-runner --help`, un caso real (`--type=validators --git-mode=changed`) y uno de error (`--type=foo`, exit 2).
6. `python -m devtools agent-context` y `rules`, más la validación headless de `agent-config-testing.md`.
7. Prueba de los hooks: un commit con un archivo de 301 líneas se rechaza en el pre-commit, y se descarta con `git reset`.

No se carga ningún modelo, así que no hace falta turno de GPU ni mediciones de audio.

## 2. Cierre

* Fichas `WARNING/003-baselines.md` y `PENDING/003-bajar-baselines.md` (con los overrides de mypy) y sus filas.
* Estado de la fila 003 en el README del lote.

## 3. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con el resumen de etapas y modos, los comandos de los hooks y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 003-test-runner`.
