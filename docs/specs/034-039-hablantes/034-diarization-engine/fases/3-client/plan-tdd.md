# Spec 034, fase 3: client

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `034-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-034/` o `tmp/spec-034/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: el usuario pega su token en la tarjeta del motor, acepta las condiciones desde el enlace, instala y ve la atribución. **AC**: AC-5, AC-6. **Depende de**: F2.

## Ciclos TDD

#### Ciclo C6: grupo, campo del token y atribución [AC-5, AC-6]

- **RED**: `client/tests/unit/src/features/engines/HfTokenField.test.tsx`
  - Sin token: el campo, el enlace e «Instalar» deshabilitado. Al guardar: `PUT` y el estado «Token guardado». «Quitar»: `DELETE`.
  - `EnginesPage.test.tsx`: el grupo «Diarización».
  - `About.test.tsx`: el texto `settings.about.diarization`.
- **GREEN**: `EnginesPage.tsx`, `HfTokenField.tsx`, `EngineCard.tsx`, «Acerca de» y los textos. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/engines/happy-hf-token.e2e.ts` | Open Engines, see Diarization group, paste token, save, install becomes enabled, remove token | AC-5 |
| `tests/e2e/engines/neg-gated-install.e2e.ts` | Install job ends with engine_gated; the card shows the accept-conditions message | AC-3, AC-5 |
