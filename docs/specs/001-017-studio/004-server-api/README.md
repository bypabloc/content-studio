# 004: server FastAPI + SQLite, cola de trabajos con SSE y CLI headless `studio`

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `004-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en `out/<herramienta>/spec-004/`, `tmp/spec-004/` o en una base en `tmp_path`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos nuevos y el borrado de `cli.py` y del CLI interactivo) |
| Rama | `feature/004-server-api` desde `origin/dev`, en `../content-studio-worktrees/004-server-api/` |
| Depende de | [003](../003-test-runner/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Que la narración y la música sean trabajos de una cola persistente en SQLite, expuestos por una API HTTP local (FastAPI con OpenAPI) con progreso por SSE, para que la UI de la 005 tenga a quién hablarle. Las mismas funciones las usa un CLI headless, `uv run studio …`, que reemplaza a `cli.py`, al menú y al asistente.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | SQLite: conexión, migraciones, `jobs` y `settings` | PEN |
| 2 | Servicios de narración y música con protocolo de progreso | PEN |
| 3 | Cola y worker con el candado de GPU | PEN |
| 4 | API: jobs, settings, catálogo, archivos y SSE, con token | PEN |
| 5 | CLI `studio` y borrado de `cli.py`, el menú y el asistente | PEN |

## Decisiones clave

* D-1: sqlite3 de la stdlib en WAL, con migraciones como lista de SQL y `PRAGMA user_version`.
* D-2: un servicio por herramienta (`services/narration.py`, `services/music.py`) que comparten la API, el worker y el CLI.
* D-3: el worker corre los trabajos de GPU de a uno con el candado en `content_studio/gpu_lock.py` (devtools lo reutiliza) y los de CPU en un pool.
* D-4: el progreso sale de líneas `@@progress {json}` en el stdout del motor y llega a la UI por SSE.
* D-5: API solo en 127.0.0.1 con token por sesión y mensajes de error con código, desde el catálogo `messages/es.json`.
* D-6: el CLI `studio` usa argparse sobre los parsers que ya existen. Salen typer, rich y questionary, salvo un grupo `legacy` para `grabar/` hasta la 007.

## WARNING y PENDING

* WARNING: `004-protocolo-progreso.md` y `004-token-sse.md` (el token va en la query para `EventSource` y `<audio>`).
* PENDING: ninguna nueva. Cierra la parte `cli/` de `002-cspell-excepciones-temporales.md`.
