# Spec 028, fase 2: La ventana se adjunta

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `028-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-028/` o `tmp/spec-028/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Tauri usa `studio api up` y deja de ser dueño del server. **AC**: AC-7, AC-9. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C5: Adjuntarse y cambiar de versión [AC-7, AC-9]

- **RED**: `client/src-tauri/src/lib.rs::tests::connect_attaches_to_running_server`
  - Given un runner falso que devuelve una línea `ready` con `url` y `token` When `connect` corre Then no asigna Job y devuelve esa conexión; con `version` distinta, primero pide `api down`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `ServerState::connect` con `api up --with-token`; `parse_ready` lee `url` y `token`; el updater corre `api down --force`. Verify: `python -m devtools test-runner --type=tauri-check`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
