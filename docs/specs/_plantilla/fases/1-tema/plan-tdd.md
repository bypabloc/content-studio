# Spec <NN>, fase 1: <tema>

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../process/WARNING/README.md) (ficha `<NN>-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-<NN>/` o `tmp/spec-<NN>/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: <qué deja funcionando esta fase>. **AC**: AC-1. **Depende de**: <nada | fase anterior>.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/test_bugs.py`.

#### Ciclo C1: <pieza> [AC-1]

- **RED**: `server/tests/<ruta espejo>/test_<archivo>.py::test_ac1_<caso>` (o un doctest en `<módulo>`)
  - WHEN <acción> THEN <resultado> [AC-1].
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `server/src/content_studio/<…>.py`: <implementación mínima>. Verify: `uv run pytest <test> -q`.
- **REFACTOR**: <qué se limpia | ninguno>.

## Matriz e2e

<Solo si esta fase crea o cambia un flujo del client. Se escribe aquí y se ejecuta en la verificación final. Si no, «no aplica».>

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/<flujo>/happy-<caso>.e2e.ts` | <pasos en inglés> | AC-1 |
| `tests/e2e/<flujo>/neg-<caso>.e2e.ts` | <...> | AC-2 |
