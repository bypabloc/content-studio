# <NN>: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Una sola vez, con todos los commits hechos y antes del push (`plan-format.md` §4). Si algo falla, se corrige con commits `fix(...)` y se repite solo lo rojo.

## 1. Batería

1. `uv run ruff check && uv run ruff format --check`
2. `uv run pytest`
3. `uv run pytest -m local` (si toca un motor o su registro).
4. `python -m devtools contexto-agentes` y `reglas` (si toca `.agents/`, `.claude/` o `AGENTS.md`), más la validación headless de `agent-config-testing.md`.
5. Corrida real de lo que cambió, con el turno: `python -m devtools turno-gpu run --trabajo=<NN>-<slug> -- python cli.py <…> --salida out/<herramienta>/spec-<NN>/` (si aplica).
6. Mediciones de cada salida (`verify-before-claiming-done.md` §2): duración, LUFS y pico, y espectrograma en `tmp/spec-<NN>/` revisado por `image-reader` contra «debe sonar / no debe sonar» de `01`.
7. CLI: `--help`, un caso real y uno de error; sin TTY no pregunta nada (si aplica).

## 2. Escucha

Las rutas de `out/` van en el reporte y en el PR para que el usuario escuche. Si la spec debía elegir entre opciones sonoras, el agente elige con el «debe sonar» de `01`, lo registra en `docs/process/WARNING/` y sigue; nada espera la escucha.

## 3. Cierre

* Fichas de `docs/process/01-done/` actualizadas si la spec es funcional.
* Toda decisión con su ficha en `docs/process/WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
* Último commit de una spec suelta: `git rm -r docs/specs/<NN>-<slug>/` y su fila de `docs/specs/README.md` (en un lote, lo hace la spec final).

## 4. PR y merge

1. `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
2. `gh pr list --head <rama>`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales), rutas de `out/` y fichas WARNING/PENDING.
3. `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close <NN>-<slug>`.
