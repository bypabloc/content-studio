# Spec 030, fase 2: API, CLI, MCP y Ajustes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `030-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-030/` o `tmp/spec-030/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Registrar carpetas desde cualquier superficie. **AC**: AC-1, AC-10, AC-9. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C6: API, CLI y MCP [AC-1, AC-10]

- **RED**: `server/tests/unit/src/content_studio/api/routes/test_inbox.py::test_ac1_post_get_pause_delete`
  - WHEN `POST /inbox/folders` con una carpeta válida THEN 201 y aparece en `GET`; la lista MCP debe tener `studio_watch_folder`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `api/routes/inbox.py`, `cli/inbox.py`, herramienta en `mcp_server/tools.py`. Verify: `uv run pytest server/tests -k inbox -q`.
- **REFACTOR**: ninguno.

#### Ciclo C7: Carpetas en Integraciones [AC-9]

- **RED**: `client/tests/unit/src/features/settings/InboxFolders.test.tsx`
  - WHEN se agrega una carpeta con «Convertir a MP3» THEN la lista la muestra; quitar pide confirmación.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: organismo en el panel y claves de 02 §5. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/settings/happy-inbox-folders.e2e.ts` | add a folder with pickPaths, choose Convert to MP3, see it listed, pause it, remove it accepting the confirm | AC-9 |
| `tests/e2e/settings/neg-inbox-missing-folder.e2e.ts` | the mock API answers folder_not_found: the dialog shows the catalog message | AC-9 |
