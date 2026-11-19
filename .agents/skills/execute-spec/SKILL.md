---
name: execute-spec
description: >
  Implementa una spec de docs/specs/ en la ventana principal, un grupo de commit a la vez, con TDD, verificación,
  commits incrementales, un PR a dev, merge y cierre del worktree. SIEMPRE invocar para ejecutar una spec. Usar cuando
  el usuario diga "ejecuta la spec", "ejecuta el plan", "implementa la spec", "implementa la fase", "execute spec".
---

# execute-spec — content-studio

La ventana principal implementa la spec de principio a fin y conserva el contexto entre tareas. Reglas: `plan-format.md`, `git-workflow.md`, `worktrees.md`, `turno-gpu.md` y el plugin `session-handoff`.

## 1. Preparación

1. Usa la spec que indique el usuario; si no indica una, lista `docs/specs/README.md` y pregunta.
2. Lee `README.md`, `01-contexto-y-decision.md` y `02-plan.md` (y el README del lote si vive en uno). Corre su «Precondición». Ordena los grupos de commit por dependencia y omite los ya hechos.
3. Worktree propio: `git fetch origin dev`, `git worktree add ../content-studio-worktrees/<NN>-<slug> -b <prefijo>/<NN>-<slug> origin/dev` y `python -m devtools worktree prepare <NN>-<slug>`; si ya existe, reutilízalo. Nunca commits en `dev` ni `main`.
4. **Handoff**: crea `tmp/handoff/<NN>-<slug>/` en el principal (PROGRESS, DECISIONS, NOTES) y el vínculo de tu sesión; `Status: in-progress`, `Phase: implementation`.
5. Resuelve contradicciones con las reglas antes de tocar archivos; lee las fichas de `docs/process/WARNING/` y `PENDING/` que cite.

## 2. Por cada grupo de commit

1. TDD (skill `tdd-workflow`): test en rojo, implementación mínima, refactor. Solo los archivos del grupo. Marca las tareas como hechas en el README de la spec.
2. Verify de cada tarea y `uv run ruff check && uv run ruff format --check && uv run pytest`. Nada que cargue un modelo por grupo.
3. Si falla, diagnostica y repite solo lo afectado; no avances con el grupo en rojo.
4. Toda disyuntiva la decides tú (la opción correcta, no la más rápida) y va a `docs/process/WARNING/<NN>-<tema>.md` con la plantilla de su README; lo diferido, a `PENDING/`. Solo preguntas con un `blocked` de `user-data`, `cost`, `credentials`, `user-stop` o `taste` (plugin `session-handoff`).
5. Commit con el mensaje exacto del grupo en `02-plan.md` tras revisar el diff contra la escalera KISS y «Fuera de alcance». Si un hook falla, corrige (skill `fix-hooks`) y repite.
6. Anota el hash en `PROGRESS.md` (Done, Current, Remaining, ETA, Next step).

## 3. Verificación final, PR y merge

1. `Phase: verification`. Corre una vez la batería de `03-verificacion-final.md`: ruff, pytest, `pytest -m local` si toca un motor, la corrida real con `gpu-turn run --job=<NN>-<slug> -- …` y duración, volumen y espectrograma de cada salida (las imágenes las abre `image-reader`). Si toca configuración de agentes, la validación headless. Lo que falle se corrige con commits `fix(...)` y se repite solo eso.
2. Último commit: fichas de `docs/process/01-done/` si la spec es funcional; en una spec suelta, `git rm -r docs/specs/<NN>-<slug>/` y su fila del índice. Antes de borrar, todo lo importante tiene su ficha en WARNING o PENDING.
3. `Phase: integration`: `git fetch origin dev` y merge de `origin/dev` en la rama si avanzó; un solo push; `gh pr list --head <rama>` y crea el PR a `dev` si no existe (cuerpo: problema, solución, cómo probar con comandos reales, fichas WARNING/PENDING).
4. `gh pr checks <n> --watch` (`Phase: external-wait` mientras tanto); con todo verde, `gh pr merge <n> --merge`.
5. `Phase: closing`: en el principal, `git switch dev && git pull` y `python -m devtools worktree close <NN>-<slug>`; `Status: done`.

## 4. Reporte final

Cada grupo con su commit y su verificación, el PR y su merge en `dev`, las fichas de WARNING y PENDING que dejó (o que no dejó ninguna) y las rutas de `out/` para que el usuario escuche.
