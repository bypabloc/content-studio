# Spec 026, fase 1: Huella de receta y «Actualizar» en Motores

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `026-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-026/` o `tmp/spec-026/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Detectar recetas que cambiaron y ofrecer la actualización sin tocar nada solo. **AC**: AC-3, AC-7. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Huella al instalar y estado `outdated` [AC-3]

- **RED**: `server/tests/unit/src/content_studio/engines/test_installer.py::test_ac3_receta_cambiada_queda_outdated`
  - Given una instalación con la huella de la receta A When la receta pasa a B Then el estado es `outdated`; hoy sale instalado.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `engines/installer.py` escribe `recipe.sha256` al terminar; `verification.py` lo compara. Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Motores muestra la actualización [AC-7]

- **RED**: `client/tests/unit/src/features/engines/EngineCard.test.tsx`
  - WHEN el motor llega `outdated` THEN se ve «Actualización disponible» y «Actualizar» lanza la instalación.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: estado y claves `engines.outdated` y `action.update` en los tres catálogos. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/engines/happy-update-outdated.e2e.ts` | open Engines, see the outdated badge, press Update, see the install job in the queue | AC-7 |
