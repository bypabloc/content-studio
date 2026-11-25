# Spec 026, fase 2: Recetas de narración

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `026-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-026/` o `tmp/spec-026/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Los siete motores TTS en su Python y librerías más altas. **AC**: AC-1, AC-2, AC-4. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C3: Recetas TTS al día [AC-1, AC-2, AC-4]

- **RED**: `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac1_every_engine_below_pinned_python_has_warning`
  - WHEN una receta usa una Python menor que `.python-version` THEN debe existir `docs/process/WARNING/026-<motor>-version.md`; hoy no existe ninguna.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: por motor, en la carpeta aislada: subir, `studio engines install <motor>`, salida corta con `studio narration tts`, medir y escribir la receta o la ficha. Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
