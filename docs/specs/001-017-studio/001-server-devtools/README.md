# 001: Python a server/, datos a server/data/ y devtools/ en la raíz

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `001-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-001/` o `tmp/spec-001/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. **Excepción pedida por el usuario**: `move-data` **mueve** (nunca copia ni borra) `narration/` y `music/` a `server/data/`, con todo su contenido.

| Campo | Valor |
| :--- | :--- |
| Tipo | refactor |
| Escala | Large (unos 45 archivos versionados, la mayoría con cambios de rutas) |
| Rama | `refactor/001-server-devtools` desde `origin/dev`, en `../content-studio-worktrees/001-server-devtools/` |
| Depende de | ninguna |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Dejar la forma de klinikae sin cambiar el comportamiento. El código Python va a `server/src/content_studio/` y sus tests a `server/tests/`. Los datos (`narration/` y `music/`, con sus venvs, motores, modelos y voces) van a `server/data/`. Las herramientas de agentes salen del paquete y pasan a `devtools/` en la raíz, invocadas con `python -m devtools`. Narración, música y CLI siguen funcionando igual.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): contexto, decisiones, fuera de alcance, AC y diagrama.
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, migración real, mediciones, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | `devtools/` en la raíz, con `move-data` y su test | PEN |
| 2 | uv workspace y código a `server/`; rutas a `server/data/` | PEN |
| 3 | Tests junto a lo que prueban; hooks, CI, `.gitignore` y reglas actualizados | PEN |
| 4 | Migración real en el principal y verificación | PEN |

## Decisiones clave

* D-1: un uv workspace en la raíz con un solo miembro, `server`. `devtools/` es un paquete stdlib sin pyproject.
* D-2: `move-data` mueve con `os.replace` y reescribe las rutas absolutas de las tres instalaciones editables, así que no hace falta recrear ningún venv.
* D-3: `cli.py` sigue en la raíz como shim (apunta a `server/src`) hasta que la 004 lo reemplace.
* D-4: `out/`, `logs/` y `tmp/` siguen en la raíz. La carpeta de datos elegible de la app llega con la 009 y la 015.

## WARNING y PENDING

* WARNING: `001-move-data.md`, la migración de los datos del usuario y cómo revertirla.
* PENDING: ninguna.
