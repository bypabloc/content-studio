# Spec 025: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `025-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-025/` o `tmp/spec-025/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run pytest -m local` | toca un motor o su registro |
| 4 | `python -m devtools test-runner --type=tauri-check` | toca `client/src-tauri/` |
| 5 | `python -m devtools agent-context` y `python -m devtools rules`, más la validación headless (`agent-config-testing.md`) | toca `.agents/`, `.claude/` o `AGENTS.md` |
| 6 | `uv run studio narration tts --model qwen-0.6b --style expert --voice <voz> --text "Prueba de la spec 025."` y `uv run studio music --model heartmula --style lofi-chill --duration 30` | siempre (AC-7) |
| 7 | Duración, LUFS y pico, y espectrograma en `tmp/spec-025/` revisado por `image-reader` | siempre (AC-7) |

## 2. Comprobaciones propias

1. `uv run python --version` dice la versión de `.python-version` [AC-1].
2. `uv tree --outdated --depth 1` no lista ninguna dependencia directa [AC-4].
3. Los dos trabajos de AC-7 terminan y su `logs/jobs/<id>.log` muestra el relanzamiento en el venv del motor [AC-7].
4. `python -m devtools bundle` y la app instalada desde el instalador nuevo, sobre una instalación previa con 3.12, arrancan y la sección Narración carga [AC-6].

## 3. Escucha

Las dos rutas de `out/` de AC-7 van en el PR; deben sonar igual que antes del cambio.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `server.md` (Historial: Python del server) e `installer.md` (versión que prepara).
- [ ] Reglas y docs actualizadas: `codigo-python.md` (el mínimo pasa a «server en `.python-version`; lo que corre en los motores, el piso de las recetas»), `stack.md` §1, `testing.md` (CI de una versión) y `AGENTS.md`; `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head chore/025-server-python`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales), rutas de `out/` y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 025-server-python`.
