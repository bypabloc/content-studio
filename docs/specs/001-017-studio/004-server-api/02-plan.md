# 004: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Los tests van en la ruta espejo (`server/tests/unit/src/content_studio/<ruta>/test_<module>.py`), con cobertura ≥ 80 % por archivo (003).

## 1. Ciclos TDD

#### Ciclo 1: base [AC-1]

- **RED**: `db/test_schema.py::test_ac1_migrate_idempotent`, `db/test_jobs.py` y `db/test_settings.py` (CRUD sobre `tmp_path`).
- **GREEN**: `db/connection.py`, `schema.py`, `jobs.py`, `settings.py` y `paths.DB`. `var/` en `.gitignore`.
- **REFACTOR**: ninguno.

#### Ciclo 2: progreso y servicios [AC-5 (parte de parseo)]

- **RED**: `common/test_progress.py` (formato de la línea) y `jobs/test_runner.py` (parsea `@@progress` de un proceso falso, actualiza el trabajo y deja el resto en `logs/jobs/<id>.log`). Más `services/test_narration.py` y `test_music.py` (`build_command` y `validate` con parámetros válidos e inválidos).
- **GREEN**: `common/progress.py`, `jobs/runner.py`, `services/{narration,music,registry}.py` y las llamadas a `progress.emit` en los `main` de narración (por bloque) y música (al empezar, por etapa del motor y al terminar).
- **REFACTOR**: ninguno.

#### Ciclo 3: candado de GPU en server [AC-4]

- **RED**: `test_gpu_lock.py`. Se toma y se libera, y si otro lo tiene, `acquire(wait=False)` devuelve `False`. Es compatible con el archivo que escribe `devtools gpu-turn`, con la misma fixture.
- **GREEN**: `content_studio/gpu_lock.py`. `devtools/gpu_turn.py` lo importa (D-3) y sus tests siguen verdes.
- **REFACTOR**: se borra el código del candado que quedó duplicado en devtools.

#### Ciclo 4: cola y worker [AC-2, AC-3, AC-4, AC-11]

- **RED**: `jobs/test_queue.py` y `jobs/test_worker.py`, con los casos de AC-2, AC-3, AC-4 y AC-11 y un servicio falso registrado en el test.
- **GREEN**: `jobs/queue.py` y `jobs/worker.py` (D-3), con la terminación del árbol de procesos (en Windows, `taskkill /T /F` como fallback).
- **REFACTOR**: ninguno.

#### Ciclo 5: API, token, catálogo y settings [AC-6, AC-7, AC-8]

- **RED**: `api/test_app.py` (401), `api/test_files.py` (403 por `..` y 200 dentro de `out/`), `api/test_jobs_api.py` (422 con `code` y `message`), `api/test_catalog.py` y `api/test_settings_api.py`.
- **GREEN**: `api/app.py` y sus rutas, `messages/es.json` y `messages.py`, y `recommended` en `ENGINES` y `MODELS` (Qwen 0.6B y ACE-Step como recomendados por defecto; decídelo con el README y anótalo en WARNING). Dependencias: `fastapi` y `uvicorn` en `server/pyproject.toml`, y `httpx` en `dev`.
- **REFACTOR**: si hay validación repetida entre API y CLI, se deja solo en `services/*.validate`.

#### Ciclo 6: SSE [AC-5]

- **RED**: `api/test_events.py`. Un suscriptor recibe `event: job` cuando el runner publica.
- **GREEN**: `api/events.py` y `GET /events`.
- **REFACTOR**: ninguno.

#### Ciclo 7: CLI `studio` y borrado del CLI interactivo [AC-9]

- **RED**: `cli/test_main.py` (help, exit 2 y sin preguntas sin TTY) y `test_structure.py::test_no_py_at_root`.
- **GREEN**: `cli/main.py` (D-6) y `studio serve`. `git rm` de `cli.py`, `cli/{app,menu,flow,widgets,args,help}.py` y los tests del asistente. Se ajustan las dependencias y el grupo `legacy`, y se saca `cli/` de `ignorePaths` de cspell.
- **REFACTOR**: ninguno.

#### Ciclo 8: reglas y docs

- **RED**: ninguno. Es documentación (AC-9 de la 001 ya cubre las rutas viejas en `test_structure`).
- **GREEN**: D-7.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/db/{__init__,connection,schema,jobs,settings}.py` | `test-runner --type=unit --files=...` |
| Crear | `server/src/content_studio/{common/progress,gpu_lock,messages}.py`, `messages/es.json` | ídem |
| Crear | `server/src/content_studio/services/{__init__,registry,narration,music}.py` | ídem |
| Crear | `server/src/content_studio/jobs/{__init__,queue,worker,runner}.py` | ídem |
| Crear | `server/src/content_studio/api/{__init__,app,events}.py`, `api/routes/{health,catalog,settings,jobs,queue,files}.py` | ídem |
| Crear | `server/src/content_studio/cli/main.py` | `uv run studio --help` |
| Modificar | `narration/tts.py`, `music/music_main.py` (emiten progreso), `narration/engines/registry.py`, `music/engines/registry.py` (`recommended`), `devtools/gpu_turn.py` | tests espejo |
| Borrar | `cli.py`, `cli/{app,menu,flow,widgets,args,help}.py`, tests del asistente | `test_structure.py` |
| Modificar | `server/pyproject.toml`, `pyproject.toml`, `uv.lock`, `.gitignore` (`var/`), `cspell.config.yaml` | `uv sync`, `spelling` |
| Modificar | reglas, `AGENTS.md`, README, `docs/process/01-done/` (+ `server.md`) | `agent-context`, `rules` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Base | AC-1 | — | `test-runner --type=unit` | [ ] |
| T2 | Progreso y servicios | AC-5 | T1 | ídem | [ ] |
| T3 | Candado de GPU | AC-4 | — | ídem | [ ] |
| T4 | Cola y worker | AC-2, AC-3, AC-4, AC-11 | T1–T3 | ídem | [ ] |
| T5 | API, token, catálogo y settings | AC-6, AC-7, AC-8 | T4 | ídem | [ ] |
| T6 | SSE | AC-5 | T5 | ídem | [ ] |
| T7 | CLI `studio` y borrados | AC-9 | T4 | `uv run studio --help \| cat` | [ ] |
| T8 | Reglas y docs | — | T7 | `agent-context`, `rules` | [ ] |
| T9 | Corridas reales | AC-10 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: base SQLite con migraciones, jobs y settings` (T1).
2. `feat: servicios de narración y música con protocolo de progreso` (T2).
3. `refactor: candado de GPU en el server, compartido con devtools gpu-turn` (T3).
4. `feat: cola de trabajos con worker, cancelar, reintentar, reordenar y pausar` (T4).
5. `feat: API local con token, catálogo, settings, trabajos y archivos` (T5).
6. `feat: progreso de trabajos por SSE` (T6).
7. `feat: CLI headless studio; se borran cli.py, el menú y el asistente` (T7).
8. `docs: reglas, AGENTS y README con el server y studio` (T8 y las fichas).
