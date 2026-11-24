# Spec 031, fase 1: Enlaces `content-studio://`

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `031-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-031/` o `tmp/spec-031/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Abrir, navegar y prellenar desde una URL, sin efectos. **AC**: AC-4, AC-5, AC-1, AC-2, AC-3. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Validación de enlaces [AC-4]

- **RED**: `client/tests/unit/src/app/external/parseExternal.test.ts`
  - WHEN llega `content-studio://new/engine.install?name=x` o una URL de 5000 caracteres THEN devuelve `ExternalError`; el módulo no existe.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `client/src/app/external/parseExternal.ts`. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Instancia única y reenvío [AC-5]

- **RED**: `client/src-tauri/src/external.rs::tests::forwards_argv_to_window`
  - Given un segundo arranque con una URL When el callback corre Then emite `external-request` con esa URL.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: plugins en `Cargo.toml` y `lib.rs`, esquema en `tauri.conf.json`. Verify: `python -m devtools test-runner --type=tauri-check`.
- **REFACTOR**: ninguno.

#### Ciclo C3: Navegar y prellenar [AC-1, AC-2, AC-3]

- **RED**: `client/tests/unit/src/app/external/useExternalRequests.test.tsx`
  - WHEN llega `new/narration` THEN Narración tiene el texto y no hubo `POST /jobs`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `useExternalRequests` y el estado de prellenado de cada sección. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/shell/happy-deeplink.e2e.ts` | emit external-request with open/music, then new/narration: the section shows the prefilled text and no job is created until Generate | AC-1, AC-3 |
| `tests/e2e/shell/neg-deeplink-invalid.e2e.ts` | emit an unknown kind: the invalid toast appears and the API gets no call | AC-4 |
