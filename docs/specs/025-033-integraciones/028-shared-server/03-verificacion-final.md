# Spec 028: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `028-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-028/` o `tmp/spec-028/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run studio <comando> --help`, un caso real y uno de error; sin TTY (`| cat`) no pregunta nada | toca el CLI |
| 4 | `python -m devtools test-runner --type=e2e` | toca el client |
| 5 | `python -m devtools test-runner --type=tauri-check` | toca `client/src-tauri/` |
| 6 | `python -m devtools app-check run` | toca la UI o el arranque de la app |
| 7 | `uv run pytest server/tests/unit/src/content_studio/api server/tests/unit/src/content_studio/jobs` | toca la API |

## 2. Comprobaciones propias

1. Sin app abierta: `uv run studio api up` → `api.json` y `Invoke-RestMethod http://127.0.0.1:41830/health -Headers @{Authorization="Bearer <token>"}` responde [AC-1, AC-2].
2. Con el server vivo, abrir la app (`bun run --cwd client tauri dev`), cerrarla y `uv run studio api status` sigue `alive` [AC-7].
3. Con `api.idle_minutes` = 1: esperar el aviso en `logs/server.log`, comprobar que `api.json` no está, y desde la app abierta generar algo: se reactiva [AC-5, AC-8].
4. `app-check` con `--binary` de una versión anterior instalada y el instalador nuevo: el server viejo se detiene y arranca el nuevo [AC-9].

## 3. Escucha

No aplica: la spec no cambia el audio generado.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `server.md` (server compartido, `studio api`) y `client.md` (Integraciones).
- [ ] Reglas y docs actualizadas: `AGENTS.md` (atajos: `studio api up`), `frontend-stack.md` (Tauri ya no es dueño del server) y `devtools.md` si `app-check` cambia cómo arranca el server; `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head feature/028-shared-server`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales) y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 028-shared-server`.
