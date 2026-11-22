# 024: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 0. Sondeo previo (T1, sin código de producto)

Antes del primer ciclo, en el worktree y sin commitear nada fuera de las fichas. Cada respuesta va a su ficha de WARNING con «Cómo comprobarla»:

| Pregunta | Cómo se responde | Ficha |
| :--- | :--- | :--- |
| ¿Tauri 2.12 pasa `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` a WebView2, o la pisa con sus argumentos por defecto? | Compilar con `tauri build --debug --no-bundle`, abrir el binario con la variable y un puerto libre, y pedir `http://127.0.0.1:<p>/json/version` | `024-cdp-webview2` (si no responde: respaldo `CONTENT_STUDIO_CDP_PORT` de D-3) |
| ¿Qué nombre de herramienta y qué JSON recibe un PreToolUse de Codex cuando usa Computer Use (`mcp__node_repl__js`, o `exec`/`js` en modo código)? ¿Dispara PreToolUse para herramientas MCP? | Un hook temporal en `tmp/spec-024/` que vuelca stdin a `tmp/spec-024/codex-event.json`, cableado en `.codex/hooks.json` del worktree, y `codex exec` con un prompt que pida `sky.list_apps()` | `024-hooks-por-agente` |
| ¿Antigravity tiene una herramienta de control del escritorio? ¿Con qué nombre llega a `.agents/hooks.json`? | Su documentación (subagente `researcher`) y el mismo volcado de evento, si el CLI está instalado | `024-hooks-por-agente` |
| ¿Codex respeta `[plugins."<id>"] enabled = false` en el `.codex/config.toml` del proyecto? | `codex exec` en el worktree con los dos plugins desactivados: `mcp__node_repl__js` no debe ofrecer `@oai/sky`, o la herramienta no aparece | `024-hooks-por-agente` |
| Claude Code: nombres de las herramientas de Computer Use | `mcp__computer-use__*` (app de escritorio) y `mcp__remote-devices__computer*` (sesión en la nube); se confirman con `claude-code-guide` | `024-hooks-por-agente` |

El hook temporal y su cableado se borran al terminar T1: no entran en ningún commit.

## 1. Ciclos TDD

#### Ciclo 1: qué bloquea el guard [AC-1, AC-2]

- **RED**: doctests de `reason(tool, payload)` en `.agents/hooks/computer_use_guard.py` y `.agents/hooks/tests/test_computer_use_guard.py::test_ac1_blocks_computer_use_tools_and_sky_code` y `::test_ac2_lets_other_tools_and_mentions_pass`. Casos: `mcp__computer-use__screenshot`, `mcp__remote-devices__computer_click`, `mcp__node_repl__js` con `await import("@oai/sky")`, `exec` con `tools.mcp__node_repl__js({code: 'sky.list_apps()'})`; negativos: `Bash` con `git commit -m "sin sky"`, `mcp__node_repl__js` con `console.log(1)`, `Read`. Falla porque el módulo no existe.
- **GREEN**: `TOOLS` (regex de nombres) y `CODE` (regex `@oai/sky|\bsky\.\w+\(`), y `reason()` devuelve el mensaje `Blocked by …` o `None`. Verify: `uv run pytest .agents/hooks/tests/test_computer_use_guard.py -q` y `uv run pytest --doctest-modules .agents/hooks/computer_use_guard.py -q`.
- **REFACTOR**: el texto del mensaje en una constante, en inglés (`textos-e-idioma.md`).

#### Ciclo 2: el evento de cada agente [AC-1]

- **RED**: `test_computer_use_guard.py::test_ac1_exit_code_per_agent` ejecuta el hook como proceso (`uv run --no-project python …`) con el JSON de Claude Code (`tool_name`, `tool_input`), el de Codex (el formato que registró T1) y el de Antigravity (`toolCall.name`, `toolCall.args`): exit 2 y stderr para los dos primeros; exit 0 y `{"decision": "deny"}` en stdout para Antigravity. Falla porque no hay `main()`.
- **GREEN**: `check(event)` extrae nombre y argumentos según el formato y `main()` responde como `shell_guard.main()`. Verify: el mismo test.
- **REFACTOR**: si `shell_guard` y `computer_use_guard` repiten la salida por agente, se extrae una función en el segundo uso solo si es idéntica. Si no, se deja (KISS: dos usos).

#### Ciclo 3: cableado en los tres agentes [AC-3]

- **RED**: `tests/validators/test_structure.py::test_ac3_computer_use_guard_wired_for_every_agent` lee `.claude/settings.json`, `.codex/hooks.json` y `.agents/hooks.json` y exige una entrada PreToolUse que ejecute `computer_use_guard.py` con el matcher de T1. Si T1 lo confirmó, exige también `enabled = false` para los dos plugins en `.codex/config.toml` (leído como texto: no hay `tomllib` en 3.10). Falla porque no hay cableado.
- **GREEN**: las tres entradas y las dos secciones de `.codex/config.toml`. Verify: `uv run pytest tests/validators/test_structure.py -q -k ac3`.
- **REFACTOR**: ninguno.

#### Ciclo 4: entorno aislado de una corrida `temp` [AC-4]

- **RED**: `devtools/tests/unit/app_check/test_env.py::test_ac4_temp_run_isolates_webview_home_db_and_target`: `prepare(root, data='temp', now=…)` devuelve la carpeta `tmp/app-check/<AAAAMMDD-HHMMSS>/` y un `env` con las cinco variables de D-3 (puerto de `free_port()`), sin tocar `os.environ`. Falla porque el paquete no existe.
- **GREEN**: `devtools/app_check/env.py` con `prepare()` y `free_port()` (socket de stdlib, como `pick_free_port` de `cli/serve.py`). Verify: `uv run pytest devtools/tests/unit/app_check/test_env.py -q`.
- **REFACTOR**: rutas desde `paths.ROOT` (`devtools.md`), nunca desde el CWD.

#### Ciclo 5: corrida `real` con copia pausada [AC-4, AC-9]

- **RED**: `test_env.py::test_ac9_real_run_copies_db_and_pauses_queue`: con una base SQLite de prueba en `tmp_path` (tabla `settings` y una fila `queued`), `prepare(…, data='real', source_db=…)` no fija `CONTENT_STUDIO_HOME`, `CONTENT_STUDIO_DB` apunta a la copia, la copia tiene `queue.paused` verdadero y la original conserva su hash y su mtime. También `::test_ac4_real_run_without_db_is_an_error`: sin base, `AppCheckError`, que `main` convierte en exit 2. Falla porque `real` no está implementado.
- **GREEN**: `sqlite3.connect(src).backup(dst)` y la escritura de `queue.paused` con `content_studio.jobs.queue.pause` importado dentro de la función (como hace `gpu-turn` con `gpu_lock`, `WARNING/004-candado-gpu`). Si importar el server desde devtools no corresponde, se escribe la fila con el mismo formato de `db/settings.py` y se anota en WARNING. Verify: `uv run pytest devtools/tests/unit/app_check/test_env.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo 6: compilar y esperar CDP, con errores en exit 2 [AC-5]

- **RED**: `devtools/tests/unit/app_check/test_launch.py::test_ac5_build_failure_is_exit_2_with_log`, `::test_ac5_missing_binary_is_exit_2` y `::test_ac5_cdp_timeout_is_exit_2_and_closes_job`, con `subprocess.run`, `subprocess.Popen` y `urllib.request.urlopen` simulados y el reloj inyectado. Falla porque `launch.py` no existe.
- **GREEN**: `build(root, env, log)` (`bun run --cwd client tauri build --debug --no-bundle`, salida al log), `binary(env)` (`<CARGO_TARGET_DIR>/debug/content-studio.exe`) y `wait_cdp(port, deadline)` (`/json/version` con `timeout` por intento hasta el plazo, sin `time.sleep`). Verify: `uv run pytest devtools/tests/unit/app_check/test_launch.py -q`.
- **REFACTOR**: el plazo (60 s) en una constante con su porqué.

#### Ciclo 7: Job Object, cierre y CLI [AC-6, AC-7, AC-5]

- **RED**: `test_launch.py::test_ac6_job_closes_on_success_failure_and_interrupt` (el handle del Job se cierra en los tres caminos; `KeyboardInterrupt` sale con 130), `::test_ac6_real_job_kills_only_its_tree` (`skipif(os.name != 'nt')`: lanza un `python -c` con un hijo dentro del Job, cierra el Job y comprueba que mueren los dos mientras un proceso ajeno sigue vivo). También `devtools/tests/unit/app_check/test_main.py::test_ac7_run_prints_one_json_line` (stdout parseable con las claves de D-8; `--help`; `--data=x` da exit 2; en POSIX, exit 2 con el mensaje de D-5) y `devtools/tests/unit/test___main__.py` con `app-check` en `COMMANDS`. Fallan porque no hay Job ni `main`.
- **GREEN**: `launch.py` con `Job` (ctypes: `CreateJobObjectW`, `SetInformationJobObject` con `JOBOBJECT_EXTENDED_LIMIT_INFORMATION`, `AssignProcessToJobObject`, `CloseHandle`) como context manager. `main.py` con argparse (`run`, `--scenario` repetible, `--data`): `prepare`, `build`, `Popen` dentro del Job, `wait_cdp`, `bun run --cwd tests/e2e playwright test -c playwright.app-check.config.ts <escenarios>` con `APP_CHECK_CDP`, `APP_CHECK_RUN` y `APP_CHECK_DATA` en el entorno, lectura de `report.json` y la línea JSON. La línea en `COMMANDS`. Verify: `uv run pytest devtools/tests/unit/app_check devtools/tests/unit/test___main__.py -q` y `python -m devtools app-check --help`.
- **REFACTOR**: `main.py`, `env.py` y `launch.py` en menos de 300 líneas cada uno.

#### Ciclo 8: fixture de CDP, solo lectura y diálogo simulado [AC-8, AC-9, AC-7]

- **RED**: dos e2e sobre el harness actual (`vite preview`, API simulada), que corren en el job `client`. `tests/e2e/app-check-support/neg-readonly-writes.e2e.ts`: con `readOnlyApi(page, API)`, un PUT de ajustes se aborta, queda en la lista de escrituras bloqueadas y un GET pasa. `tests/e2e/app-check-support/happy-pick-paths.e2e.ts`: con `pickPaths(page, ['C:/x.wav'])` sobre el `invoke` simulado, Importar recibe esa ruta y `get_connection` sigue yendo al `invoke` original. Fallan porque los helpers no existen.
- **GREEN**: `tests/e2e/app-check/support/readonly.ts` (`readOnlyApi`), `tests/e2e/app-check/support/tauri.ts` (`pickPaths`, D-6) y `tests/e2e/app-check/fixture.ts`. La fixture extiende `test` de Playwright: `connectOverCDP(process.env.APP_CHECK_CDP)`, toma `contexts()[0].pages()[0]`, aplica `readOnlyApi` si `APP_CHECK_DATA === 'real'`, junta errores de consola, `pageerror` y 5xx, y al final escribe su parte de `report.json`. Después `tests/e2e/playwright.app-check.config.ts` (D-7), `tests/e2e/app-check/smoke.check.ts` (secciones de `navItems()` por su enlace, en claro y en oscuro) y `tests/e2e/app-check/dialog-pick.check.ts`. Verify: `python -m devtools test-runner --type=e2e`. Los `.check.ts` se prueban en la verificación final.
- **REFACTOR**: si `support/app.ts` y `app-check/support/tauri.ts` repiten la regla de `multiple === false`, se extrae a `support/dialog.ts` y la usan los dos.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `.agents/hooks/computer_use_guard.py` | `uv run pytest .agents/hooks -q` |
| Crear | `.agents/hooks/tests/test_computer_use_guard.py` | ídem |
| Modificar | `.claude/settings.json` (PreToolUse) | `uv run pytest tests/validators/test_structure.py -q -k ac3` |
| Modificar | `.codex/hooks.json` (PreToolUse) | ídem |
| Modificar | `.agents/hooks.json` (Antigravity) | ídem |
| Modificar | `.codex/config.toml` (plugins de Computer Use desactivados, si T1 lo confirma) | ídem |
| Modificar | `tests/validators/test_structure.py` | ídem |
| Crear | `devtools/app_check/__init__.py`, `main.py`, `env.py`, `launch.py` | `uv run pytest devtools/tests/unit/app_check -q` |
| Crear | `devtools/tests/unit/app_check/test_main.py`, `test_env.py`, `test_launch.py` | ídem |
| Modificar | `devtools/__main__.py` (`COMMANDS`) y `devtools/tests/unit/test___main__.py` | `python -m devtools --help` |
| Crear | `tests/e2e/playwright.app-check.config.ts` | verificación final |
| Crear | `tests/e2e/app-check/fixture.ts`, `support/readonly.ts`, `support/tauri.ts` | `python -m devtools test-runner --type=e2e` |
| Crear | `tests/e2e/app-check/smoke.check.ts`, `dialog-pick.check.ts` | verificación final |
| Crear | `tests/e2e/app-check-support/neg-readonly-writes.e2e.ts`, `happy-pick-paths.e2e.ts` | `python -m devtools test-runner --type=e2e` |
| Modificar | `client/src-tauri/src/lib.rs` (solo si T1 activa el respaldo de D-3) | `python -m devtools test-runner --type=tauri-check` |
| Modificar | `.agents/rules/verify-before-claiming-done.md`, `devtools.md`, `frontend-stack.md`, `.agents/skills/devtools/SKILL.md` y sus copias en `.claude/` | `python -m devtools rules` y `agent-context` |
| Modificar | `AGENTS.md` (Reglas y Atajos) | `python -m devtools agent-context` |
| Modificar | `.gitignore` (solo si `tmp/app-check/` no queda cubierto por `tmp/`) | `git check-ignore tmp/app-check/x` |
| Crear | `docs/process/WARNING/024-*.md`, `docs/process/PENDING/024-allowlist-computer-use.md` y sus filas | — |

Cada `.py`, `.ts` y `.rs` de fuente queda en 300 líneas o menos, y cada test en 800 (`file-size.json`). Los `.py` nuevos de `devtools/` tienen su espejo en `devtools/tests/unit/`. Si `launch.py` baja del 80 % de cobertura en Linux, porque el Job solo corre en Windows, se agrega al baseline con su ficha, como `WARNING/004-cobertura-linux-gpu-lock`.

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Sondeo (§0); fichas `024-cdp-webview2` y `024-hooks-por-agente` | AC-1, AC-3, AC-7 | — | las fichas responden las cinco preguntas | [ ] |
| T2 | `computer_use_guard.py` y su test (ciclos 1 y 2) | AC-1, AC-2 | T1 | `uv run pytest .agents/hooks -q` | [ ] |
| T3 | Cableado en los tres agentes y `.codex/config.toml` (ciclo 3) | AC-3 | T1, T2 | `uv run pytest tests/validators/test_structure.py -q` y `uv run pytest .claude/hooks/tests/test_hooks.py .agents/hooks -q` | [ ] |
| T4 | `env.py`, modo `temp` (ciclo 4) | AC-4 | — | `uv run pytest devtools/tests/unit/app_check/test_env.py -q` | [ ] |
| T5 | `env.py`, modo `real` (ciclo 5) | AC-4, AC-9 | T4 | ídem | [ ] |
| T6 | `launch.py`: compilar y esperar CDP (ciclo 6) | AC-5 | T4 | `uv run pytest devtools/tests/unit/app_check/test_launch.py -q` | [ ] |
| T7 | Job Object, `main.py` y `COMMANDS` (ciclo 7) | AC-5, AC-6, AC-7 | T5, T6 | `uv run pytest devtools/tests/unit -q` y `python -m devtools app-check --help` | [ ] |
| T8 | Fixture, helpers, configuración y escenarios (ciclo 8); respaldo de `lib.rs` si T1 lo pidió | AC-7, AC-8, AC-9 | T7 | `python -m devtools test-runner --type=e2e`; los `.check.ts`, verificación final | [ ] |
| T9 | Reglas, skill, `AGENTS.md`, `rules --sync` y validación headless (AC-10); ficha `PENDING/024-allowlist-computer-use` | AC-10 | T3, T8 | `python -m devtools rules`, `agent-context` y `tmp/config-tests/024-app-check.json` | [ ] |

## 4. Commits

En Conventional Commits en español, en orden. Cada uno deja verdes `uv run ruff check`, `uv run ruff format --check` y `uv run pytest`, y el pre-commit (`test-runner` sobre lo staged).

1. `docs: spec 024 (app-check y Computer Use prohibido)`: esta carpeta y su fila del índice.
2. `docs: sondeo de CDP y de hooks por agente en la 024`: T1 (las dos fichas WARNING y sus filas).
3. `feat: bloquea Computer Use en Claude Code, Codex y Antigravity`: T2 y T3.
4. `feat: app-check arma una corrida aislada (temp y real)`: T4 y T5.
5. `feat: app-check compila, abre y cierra la app del worktree`: T6 y T7.
6. `feat: escenarios de app-check por CDP con diálogo simulado y solo lectura`: T8.
7. `docs: reglas y skill de app-check; Computer Use prohibido`: T9, con `N/N PASS` en el cuerpo.
8. `docs: cierre de la 024`: `git rm -r docs/specs/024-app-check/` y su fila del índice (spec técnica: no toca `01-done/`).
