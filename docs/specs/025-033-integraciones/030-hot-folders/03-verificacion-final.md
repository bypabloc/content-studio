# Spec 030: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `030-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-030/` o `tmp/spec-030/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `uv run studio <comando> --help`, un caso real y uno de error; sin TTY (`| cat`) no pregunta nada | toca el CLI |
| 4 | `python -m devtools test-runner --type=e2e` | toca el client |
| 5 | `python -m devtools app-check run` | toca la UI o el arranque de la app |
| 6 | Duración del original y del resultado con `ffprobe` | siempre |

## 2. Comprobaciones propias

1. Registrar `tmp/spec-030/entrada` con `uv run studio inbox add tmp/spec-030/entrada --kind media.convert --param target=mp3`, copiar un `.wav` con PowerShell `Copy-Item` y ver `done/<nombre>/` con el `.mp3` y el recibo [AC-2, AC-4].
2. Copiar un `.wav` grande con `robocopy` (escritura lenta): no se toma hasta terminar [AC-3].
3. Apagar el server, soltar dos archivos, `uv run studio api up`: se procesan esos dos y ninguno viejo [AC-7].
4. Si OneDrive está disponible, repetir el primer paso en una carpeta sincronizada; si no, ficha PENDING.

## 3. Escucha

No aplica: la spec no cambia el audio generado.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `integrations.md` (carpetas de entrada) y `library.md` (diferencia con las carpetas vigiladas).
- [ ] Reglas y docs actualizadas: `AGENTS.md` (atajo `studio inbox`) y `command-output.md` (dónde quedan los resultados de una carpeta de entrada); `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head feature/030-hot-folders`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales), rutas de `out/` y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 030-hot-folders`.


## 5. Resultados (2026-11-25, commit 33576cf)

| Comprobación | Resultado |
| :--- | :--- |
| `ruff check` y `ruff format --check` | pasan |
| `test-runner --type=all` | pasa; la etapa `client-typecheck` estaba roja y se corrigió (tipo del mock) |
| `studio inbox --help`, alta real, alta con error y `list \| cat` | ayuda en inglés; alta exit 0 con el registro; ruta inexistente exit 2 con `inbox_path_not_found`; sin TTY no pregunta |
| Soltar `toma.wav` (3,000 s) con el server | `done/toma.wav/` con `converted.mp3` de 3,056 s (±0,06 s) y `toma.wav.result.json`; `processing/` vacío [AC-2, AC-4] |
| Audio inválido | `failed/lento.wav/` con `lento.wav.error.json` (`process_failed`) [AC-5] |
| Archivo que cambia cada 0,5 s durante 8 s | no se toma mientras cambia; al quedar completo, se procesa en 6 s [AC-3] |
| Dos archivos soltados con el server apagado | se procesan al levantarlo; cinco trabajos en total, sin reprocesar [AC-7] |
| `keep_awake` con un minuto de inactividad | con la carpeta activa sigue encendido a los 80 s; sin `keep_awake` se apaga a los 92 s [AC-8] |
| `app-check` smoke (run `20261125-071959`) | claro y oscuro pasan; sin errores de consola |
| `app-check` escenario `carpetas-entrada` (run `20261125-072235`) | claro y oscuro pasan; sin errores ni 4xx |
| `test-runner --type=e2e` completo | 91 de 92 en una corrida; la prueba de axe en en/pt falló en 2 de 5 corridas (PENDING `030-axe-language-intermitente`); `tests/e2e/settings`, 13 de 13 |

Lo que no se probó aquí: el cliente MCP real con `studio_watch_folder` (AC-10 queda cubierto por la prueba del puente
con API falsa), el `.job.json` en el flujo real (AC-6, cubierto por la prueba unitaria) y OneDrive o una unidad de red
(PENDING `030-unidades-de-red`).

Las pruebas de `keep_awake` y de `api up/down` usaron `tmp/spec-030/content-studio.db` con `api.idle_minutes = 1`; la
base del usuario no se tocó.
