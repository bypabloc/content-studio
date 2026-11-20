# 007: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Una sola vez, con todos los commits hechos y antes del push. No carga modelos: no pide turno de GPU.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e` y `--type=budget` (anota el delta del bundle en el PR).
2. `python -m devtools rules` y `python -m devtools agent-context` (cambió `ui-components.md`), más la validación headless de `agent-config-testing.md`.

## 2. App real

1. `bun run --cwd client tauri dev`: cambia el tema tres veces desde el botón del pie, colapsa y expande la sidebar, recarga y comprueba que se mantiene, recorre los botones con Tab y mira cada tooltip.
2. Capturas del shell, la cola con trabajos y Narración, en claro y en oscuro, expandida y colapsada, en `tmp/spec-007/`. Las revisa `image-reader`: iconos visibles en los dos temas, alineados con el texto, sin recortes y con el tooltip dentro de la ventana.

## 3. Cierre

* Fichas WARNING `007-lucide-version.md` y `007-tooltip-propio.md`, con su fila.
* `docs/process/01-done/client.md` (o la ficha del client que exista) con los iconos y el criterio.
* Estado de la fila 007 en el README del lote.

## 4. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con el delta del budget, las capturas descritas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 007-icons`.
