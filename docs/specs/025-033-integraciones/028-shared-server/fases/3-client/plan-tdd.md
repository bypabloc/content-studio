# Spec 028, fase 3: Reconexión y Ajustes > Integraciones

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `028-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-028/` o `tmp/spec-028/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: La UI sobrevive al apagado por inactividad y muestra cómo conectarse. **AC**: AC-8, AC-11. **Depende de**: fase 2.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C6: Reconexión transparente [AC-8]

- **RED**: `client/tests/unit/src/shared/api/client.test.ts`
  - WHEN `fetch` falla por red THEN se vuelve a pedir `get_connection` y se reintenta una vez; un 500 no reintenta.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `shared/api/client.ts` y `events.ts`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C7: Ajustes > Integraciones [AC-11]

- **RED**: `client/tests/unit/src/features/settings/IntegrationsPanel.test.tsx`
  - WHEN se abre el panel THEN muestra URL, puerto y minutos; «Cambiar token» pide confirmación.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: panel con átomos y moléculas, claves de 02 §5, rutas `GET/PUT /settings`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/settings/happy-integrations.e2e.ts` | open Settings > Integrations, copy the token, change the port, rotate the token accepting the confirm | AC-11 |
| `tests/e2e/shell/happy-server-wakes.e2e.ts` | the mock API drops the connection, the user presses Generate, get_connection is called again and the job appears | AC-8 |
| `tests/e2e/settings/neg-rotate-cancel.e2e.ts` | rotate the token and dismiss the confirm: the token stays | AC-11 |
