# Spec 027: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `027-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-027/` o `tmp/spec-027/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `python -m devtools test-runner --type=e2e` | toca el client |
| 4 | `python -m devtools test-runner --type=tauri-check` | toca `client/src-tauri/` |
| 5 | `python -m devtools app-check run` | toca la UI o el arranque de la app |
| 6 | `python -m devtools agent-context` y `python -m devtools rules`, más la validación headless (`agent-config-testing.md`) | toca `.agents/`, `.claude/` o `AGENTS.md` |
| 7 | `python -m devtools bundle` y el instalador con `tauri build` | toca el crate |

## 2. Comprobaciones propias

1. `bun outdated` en cada workspace sin filas de dependencias directas [AC-1].
2. El reporte de `app-check` sin fallos y las capturas revisadas por `image-reader` iguales a las de antes [AC-4].
3. `client/dist` dentro del presupuesto (etapa `budget`) [AC-3].

## 3. Escucha

No aplica: la spec no cambia el audio generado.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `client.md` (Historial: versiones).
- [ ] Reglas y docs actualizadas: `frontend-stack.md` (tabla y edición de Rust); `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head chore/027-client-deps`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales) y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 027-client-deps`.
