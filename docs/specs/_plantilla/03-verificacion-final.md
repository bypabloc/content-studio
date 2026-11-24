# Spec <NN>: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../process/WARNING/README.md) (ficha `<NN>-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-<NN>/` o `tmp/spec-<NN>/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo. Borra los pasos que no apliquen.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run pytest -m local` | toca un motor o su registro |
| 4 | `python -m devtools agent-context` y `python -m devtools rules`, más la validación headless (`agent-config-testing.md`) | toca `.agents/`, `.claude/` o `AGENTS.md` |
| 5 | `uv run studio <comando> …` (toma el candado solo) o `python -m devtools gpu-turn run --job=<NN>-<slug> -- <cmd>` | cambia lo que genera audio |
| 6 | Duración, LUFS y pico, y espectrograma en `tmp/spec-<NN>/` revisado por `image-reader` (`verify-before-claiming-done.md` §2) | hay salidas de audio |
| 7 | `uv run studio <comando> --help`, un caso real y uno de error; sin TTY no pregunta nada | toca el CLI |
| 8 | `python -m devtools test-runner --type=e2e` | toca el client |

## 2. Comprobaciones propias

<Lo que la batería no cubre: prueba real paso a paso, resultado esperado por AC.>

1. <Paso> → <resultado> [AC-1].

## 3. Escucha

Las rutas de `out/` van en el reporte y en el PR para que el usuario escuche. Si la spec debía elegir entre opciones sonoras, el agente elige con el «debe sonar» de `01`, lo registra en `docs/process/WARNING/` y sigue; nada espera la escucha.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Spec funcional: fichas de `docs/process/01-done/` actualizadas («Qué hace hoy», «Dónde vive», Historial, `actualizada`).
- [ ] Spec suelta: `git rm -r docs/specs/<NN>-<slug>/` y su fila de `docs/specs/README.md` en el último commit. Spec de lote: deja sus fases en `IMP`.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head <rama>`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales), rutas de `out/` y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close <NN>-<slug>`.
