# Spec 027, fase 1: Dependencias de JavaScript

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `027-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-027/` o `tmp/spec-027/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Client, e2e y raíz en la última versión. **AC**: AC-1, AC-2, AC-3. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Versiones exactas y al día [AC-1, AC-2, AC-3]

- **RED**: `tests/validators/test_pins.py::test_ac1_versiones_exactas`
  - WHEN un manifiesto tiene `^` o `~` THEN el test falla; se escribe primero con un caso de prueba que lo tenga.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `bun update --latest` en `client/`, `tests/e2e/` y la raíz; quitar rangos; adaptar las APIs que cambien. Verify: `bun run --cwd client build && bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
