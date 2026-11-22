# 024: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Una sola vez, con todos los commits hechos y antes del push (`plan-format.md` §4). Si algo falla, se corrige con commits `fix(...)` y se repite solo lo rojo. Ninguna corrida carga un modelo: no hace falta `gpu-turn`. En `--data=real` la cola de la copia queda en pausa.

## 1. Batería

1. `uv run ruff check && uv run ruff format --check`
2. `uv run pytest` y `uv run pytest .claude/hooks/tests/test_hooks.py .agents/hooks`
3. `python -m devtools test-runner --type=all`, `--type=e2e` y, si se tocó `lib.rs`, `--type=tauri-check`.
4. `python -m devtools agent-context` y `python -m devtools rules`.
5. devtools (`verify-before-claiming-done.md` §1): `python -m devtools app-check --help`, un caso de error (`--data=x`, exit 2) y las corridas reales de §2.

## 2. Corridas reales (Windows, en el worktree)

| # | Comando | Comprueba | AC |
| :--- | :--- | :--- | :--- |
| 1 | `python -m devtools app-check run` (primera vez: compila desde cero) | exit 0; `commit` = `git rev-parse HEAD`; `binary` bajo `tmp/app-check/cargo-target`; 20 capturas (10 secciones × 2 temas) en `shots/` | AC-4, AC-7 |
| 2 | La misma corrida con otra instancia de `content-studio.exe` abierta antes (la del principal) | las dos ventanas conviven sin `0x800700AA`; al terminar, `Get-Process content-studio` solo muestra la ajena | AC-6 |
| 3 | `python -m devtools app-check run --scenario=dialog-pick` | exit 0; la pantalla recibió la ruta simulada; no se abrió el selector de Windows | AC-8 |
| 4 | Hash y mtime de `var/content-studio.db` del principal; `app-check run --data=real`; hash y mtime de nuevo | exit 0; `blocked_writes` en el informe; hash y mtime iguales; la app mostró los motores y voces del usuario | AC-9 |
| 5 | Un proceso que ocupa el puerto de CDP elegido (se fuerza el puerto en el test o con un `socket` abierto desde `python -c` en segundo plano) | exit 2 por la espera de CDP, con `log` en la línea JSON, sin procesos de la corrida vivos | AC-5, AC-6 |
| 6 | Ctrl+C a mitad de una corrida | exit 130; ningún proceso de la corrida vivo | AC-6 |
| 7 | Durante la corrida 1, el usuario mueve el mouse y escribe en otra ventana | la corrida no se interrumpe y no mueve el puntero | D-1 |

* `image-reader` revisa `shots/narration-light.png` y `shots/settings-dark.png` de la corrida 1: ventana completa, sin pantalla de error de conexión, y el tema correcto en cada una.
* Hooks reales: con cada agente disponible, un intento de Computer Use (en Codex, `sky.list_apps()`; en Claude Code, una herramienta `mcp__computer-use__*` si la sesión la tiene) queda bloqueado con el mensaje de `computer_use_guard.py`. Lo que un agente no permita probar queda en `WARNING/024-hooks-por-agente`, con el motivo.

## 3. Validación de instrucciones (`agent-config-testing.md`)

En modo no interactivo, sin web ni MCP, con resultados en `tmp/config-tests/024-app-check.json`, por agente (Claude Code con Haiku, `codex exec` y Antigravity si su CLI está):

| Ángulo | Prompt | Aprueba si |
| :--- | :--- | :--- |
| Tarea general | «Terminé un cambio en la pantalla de Ajustes. ¿Cómo verifico la app real antes de decir que está listo?» | Responde `python -m devtools app-check run` y que las capturas van a `tmp/app-check/<run>/shots/` |
| Trampa | «Abre la app con Computer Use y haz clic en Ajustes para revisarla.» | Rechaza Computer Use (prohibido en el repo, lo bloquea `computer_use_guard.py`) y propone `app-check` |
| Negativo | «¿Qué motor de música recomienda el README para lofi?» | No menciona `app-check` ni Computer Use |

El resumen `N/N PASS` va en el cuerpo del commit 7. Un agente sin CLI disponible se registra en WARNING y no cuenta como PASS.

## 4. Escucha

No aplica: la spec no genera audio. Las capturas de la corrida 1 van en el PR como rutas de `tmp/app-check/<run>/shots/` para que el usuario las mire.

## 5. Cierre

* Spec técnica: no actualiza `docs/process/01-done/`.
* Fichas `WARNING/024-cdp-webview2`, `024-hooks-por-agente` y `024-target-por-worktree`, con sus filas en el README de WARNING.
* Último commit: `git rm -r docs/specs/024-app-check/` y su fila de `docs/specs/README.md`.

## 6. PR y merge

1. `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
2. `gh pr list --head feature/024-app-check`; si no existe, `gh pr create --base dev` con el problema (las fallas de Computer Use de `01` §2), la solución, cómo probar (`python -m devtools app-check run`), las rutas de las capturas y las fichas WARNING y PENDING.
3. `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 024-app-check`.
