# 004: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Precondición

La 003 está fusionada: `git show origin/dev:devtools/test_runner/main.py` existe y `python -m devtools test-runner --type=all` pasa en `origin/dev`.

## 2. Contexto

* Después de la 002 y la 003, `cli.py` (shim con PEP 723) llama a `content_studio.cli` (Typer, menú, asistente, widgets), que llama a los `main` de `narration/tts.py` y `music/music_main.py`. Cada `main` se relanza en el venv de su motor con `common/process.py`.
* Los parsers de narración y música (`parser.py`) son livianos y con stdlib. Los registros (`ENGINES`, `MODELS`) tienen venv, módulo, clase y licencia. No marcan una opción recomendada.
* El candado de GPU vive en `devtools/gpu_turn.py` (`tmp/turno-gpu/` del principal, con exit 1 si está ocupado).
* Las salidas van a `out/narration/` y `out/music/`, o a `--output` y `--folder`.
* Las decisiones del lote: SQLite con `jobs` y `settings`, la cola con cancelar, reintentar, reordenar y pausar, una carpeta por trabajo, el historial que no se borra solo, solo 127.0.0.1 con token, y el CLI `studio`.

## 3. Solución

* **D-1: base**. `content_studio/db/` tiene `connection.py` (`connect(path)` con `PRAGMA journal_mode=WAL`, `foreign_keys=ON` y `busy_timeout=5000`), `schema.py` (lista `MIGRATIONS` de SQL y `migrate(conn)` con `PRAGMA user_version`), `jobs.py` y `settings.py` (funciones, sin ORM). La ruta es `paths.DB = ROOT / 'var' / 'content-studio.db'` en modo dev (con `var/` gitignoreado). La 009 y la 015 la mueven a la carpeta de datos de la app.

  ```sql
  CREATE TABLE jobs (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, resource TEXT NOT NULL CHECK (resource IN ('gpu','cpu')),
    status TEXT NOT NULL CHECK (status IN ('queued','running','done','error','cancelled')),
    position INTEGER NOT NULL, params TEXT NOT NULL, output_dir TEXT, result TEXT,
    error_code TEXT, error_detail TEXT, progress REAL NOT NULL DEFAULT 0, stage TEXT,
    created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT);
  CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
  ```

  **La base solo guarda metadatos** (decisión del usuario): rutas, parámetros, estados, preferencias y cachés. Nunca guarda audio, video ni contenido binario, ni siquiera picos codificados en base64 (eso va como JSON de números o en un archivo de caché en disco). `test_schema.py::test_no_blob_columns` recorre `PRAGMA table_info` de cada tabla después de todas las migraciones y falla si alguna columna es `BLOB`. Lo mismo aplica a las migraciones de las specs siguientes.

  Las preferencias de los selectores se guardan como `settings` con clave `<sección>.<campo>` (`narration.model`), y `queue.paused` también vive ahí. Se descartó un ORM porque son dos tablas y la stdlib alcanza.
* **D-2: servicios**. `content_studio/services/narration.py` y `music.py` exponen `build_command(params) -> list[str]` (el `main` del motor en su venv, con flags de la 002 y `--output <output_dir>`) y `validate(params) -> list[Error]` (reusan el parser). `services/registry.py` tiene `SERVICES = {'narration': ..., 'music': ...}`: un dict de funciones, sin clases, porque no hay comportamiento polimórfico que lo justifique. La carpeta de salida es `out/<kind>/<AAAA-MM-DD>-<id>-<slug>/` con `params.json`. Las secciones de las specs siguientes agregan su servicio con una línea.
* **D-3: cola y worker**. `content_studio/jobs/queue.py` tiene `enqueue`, `cancel`, `retry` (crea un trabajo nuevo con los mismos `params`), `reorder(ids)`, `pause` y `resume`. `jobs/worker.py` es un hilo que toma el próximo `queued` por `position`. Para `resource='gpu'` toma el candado (`content_studio/gpu_lock.py`, con el mismo formato de archivo que hoy usa `devtools/gpu_turn.py`, que pasa a importarlo agregando `server/src` al `sys.path`: es stdlib, así que devtools sigue siendo stdlib), corre de a uno y, si el candado lo tiene otra sesión, espera sin bloquear los trabajos de CPU. Para `resource='cpu'` usa un pool de `max(1, os.cpu_count() // 2)`. Cancelar un trabajo en curso hace `terminate()` y, a los 5 s, `kill()` del árbol de procesos, y libera el candado. Al arrancar, los `running` que quedaron de una caída pasan a `error` con `error_code='interrupted'`.
* **D-4: progreso**. Los `main` de narración y música imprimen `@@progress {"p": 0.42, "stage": "block 3/7"}` en stdout (con un helper `common/progress.py`, sin TTY ni colores). `jobs/runner.py` parsea esas líneas, actualiza `progress` y `stage` y publica el evento. El resto del stdout y el stderr van a `logs/jobs/<id>.log`. `api/events.py` mantiene una lista de colas `asyncio.Queue`, una por suscriptor, y `GET /events` es un `StreamingResponse` `text/event-stream` con eventos `job` (un trabajo) y `queue` (orden y pausa). Se descartó `sse-starlette` porque la implementación son unas 30 líneas y no justifica una dependencia.
* **D-5: API** (`content_studio/api/`). `app.py` (`create_app(db_path, token)`) y las rutas `health`, `catalog`, `settings`, `jobs`, `queue`, `files` y `events`. Endpoints: `GET /health`, `GET /catalog/{narration,music}` (motores, estilos, voces, `recommended`, licencia, instalado), `GET|PUT /settings/{key}`, `POST /jobs`, `GET /jobs?status=&kind=`, `GET /jobs/{id}`, `POST /jobs/{id}/cancel|retry`, `PUT /queue/order`, `POST /queue/pause|resume`, `GET /files?path=` (solo dentro de `out/` y de los datos de referencia, con resolución de la ruta contra la raíz permitida para impedir `..`) y `GET /events`. Hay un token aleatorio (`secrets.token_urlsafe(32)`) por arranque. La API lo exige en `Authorization: Bearer`, y en `?token=` solo para `/events` y `/files`, porque `EventSource` y `<audio>` no mandan headers. Escucha solo en `127.0.0.1`. Los errores son `{"code": "engine_not_installed", "params": {...}, "message": "<texto del catálogo>"}`, con el texto sacado de `content_studio/messages/es.json` por `messages.t(code, **params)`. El registro de motores agrega `recommended: bool` a una opción por selector. `studio serve --port <n> --token <t>` (o `--port 0`) imprime `{"ready": {"port": n}}` en una línea cuando escucha, que es lo que lee Tauri en la 005.
* **D-6: CLI `studio`** (`content_studio/cli/main.py`). Usa argparse con los subcomandos `narration tts`, `narration voices`, `music` y `serve`, más `jobs list|cancel|retry`, y toma los parsers de cada servicio. Corre el trabajo en su mismo proceso, con el mismo candado, y lo registra en `jobs` (así el historial incluye lo que corre el CLI), mostrando el progreso en stderr. Nunca pregunta nada. `[project.scripts] studio = "content_studio.cli.main:main"`. Se borran `cli.py` de la raíz, `cli/{app,menu,flow,widgets,args,help}.py` (los nombres de la 002) y `server/tests/**/test_assistant*`. Los tests del CLI se reescriben contra `studio`. typer, rich y questionary salen de `dependencies`, y `rich` y `questionary` quedan en el grupo `legacy`, que solo usa `narration/grabar/` hasta la 007. `test_structure.py` exige que no haya `.py` en la raíz.
* **D-7: reglas y docs**. Se actualizan `AGENTS.md` (atajos con `uv run studio`), `codigo-python.md` (cómo agregar un servicio en vez de un comando del CLI), `stack.md` (FastAPI, uvicorn y SQLite), `verify-before-claiming-done.md` y `command-output.md` (rutas por trabajo y `logs/jobs/`), `turno-gpu.md` (el worker respeta el candado), los README de datos y `docs/process/01-done/`, más una ficha nueva `server.md`. Después, `python -m devtools rules --sync`.

## 4. Fuera de alcance

* La UI, Tauri y la generación de tipos TS: los hace la 005.
* Voces (construir desde la API) y grabar: los hace la 007. `narration voices` queda en el CLI como hoy.
* Instalar motores desde la API: lo hace la 009. `catalog` solo informa si está instalado.
* La carpeta de datos elegible y `%LOCALAPPDATA%`: la hacen la 009 y la 015.
* El acceso por la red local: el usuario eligió solo este equipo.

## 5. Criterios de aceptación

* **AC-1**: Given una base nueva When se llama a `migrate` dos veces Then `user_version` = 1, existen `jobs` y `settings`, no falla y ninguna columna es `BLOB`. Lo verifica: `test_schema.py` (incluido `test_no_blob_columns`).
* **AC-2**: Given tres trabajos `queued` When se reordenan como `[3,1,2]` y se pausa la cola Then el worker no arranca ninguno. Al reanudar, arranca el 3. Cancelar el 1 mientras espera lo deja `cancelled` sin correrlo. Lo verifica: `test_queue.py` y `test_worker.py`, con un servicio falso que corre `python -c` y emite `@@progress`.
* **AC-3**: Given un trabajo de GPU en curso con un proceso falso que duerme When se cancela Then el proceso termina en menos de 6 s, el trabajo queda `cancelled` y el candado se libera. `retry` crea un trabajo nuevo con los mismos `params`. Lo verifica: `test_worker.py`.
* **AC-4**: Given dos trabajos de GPU y uno de CPU When el worker corre Then los de GPU nunca se superponen y el de CPU corre en paralelo. Lo verifica: `test_worker.py`, con marcas de tiempo.
* **AC-5**: WHEN un proceso imprime `@@progress {"p":0.5,"stage":"x"}` THEN `jobs.progress` = 0.5 y un suscriptor de `/events` recibe `event: job` con ese progreso. Lo verifica: `test_events.py` (TestClient en streaming).
* **AC-6**: WHEN se llama a cualquier endpoint sin token o con uno inválido THEN responde 401, y `/files?path=../../etc` responde 403. Lo verifica: `test_app.py` y `test_files.py`.
* **AC-7**: WHEN se hace `POST /jobs` con un motor que no está instalado o un estilo inválido THEN responde 422 con `code` y `message` en español del catálogo. Lo verifica: `test_jobs_api.py`.
* **AC-8**: WHEN se hace `GET /catalog/narration` THEN cada selector tiene exactamente una opción con `recommended: true`, y `PUT /settings/narration.model` persiste y `GET` la devuelve. Lo verifica: `test_catalog.py` y `test_settings_api.py`.
* **AC-9**: WHEN se corre `uv run studio --help`, `studio narration tts --help` y `studio music --help` sin TTY THEN muestran los subcomandos y flags sin preguntar nada. `studio music --model foo` sale con exit 2, y en la raíz no queda ningún `.py`. Lo verifica: `test_cli_main.py` y `test_structure.py`.
* **AC-10**: WHEN se corren `studio narration tts …` y `studio music … --duration 15`, y además se encola lo mismo por la API con el server arriba (`studio serve --port 0`) THEN las cuatro salidas quedan en `out/<kind>/<fecha>-<id>-<slug>/` con `params.json`, los trabajos aparecen en `GET /jobs` como `done` y la música dura 15 s ± 0,5 s. Lo verifica: la verificación final.
* **AC-11**: WHEN arranca el server con un trabajo `running` que quedó de una caída THEN el trabajo pasa a `error` con `error_code='interrupted'`. Lo verifica: `test_worker.py`.

## 6. Diagrama

```mermaid
flowchart LR
    UI[client 005] -- HTTP + token --> API[FastAPI 127.0.0.1]
    CLI[studio CLI] --> SVC
    API --> Q[(SQLite jobs/settings)]
    W[worker] --> Q
    W -- gpu: de a uno + gpu_lock --> SVC[services: narration, music]
    W -- cpu: pool --> SVC
    SVC -- venv del motor --> E[engine main] -- "@@progress" --> W
    W -- evento --> SSE[/events] --> UI
```

## 7. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| `out/narration/<fecha>-<id>-*/` | Igual que el `narration tts` de antes, con el mismo motor, voz y estilo | Cortarse si se encola por la API |
| `out/music/<fecha>-<id>-*/` | 15 s ± 0,5 s, con LUFS en el rango del README | Voz o silencios |
