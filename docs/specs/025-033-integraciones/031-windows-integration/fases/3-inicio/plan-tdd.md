# Spec 031, fase 3: Inicio con Windows

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `031-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-031/` o `tmp/spec-031/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: El server puede arrancar al iniciar sesión. **AC**: AC-8. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C6: Valor `Run` de HKCU [AC-8]

- **RED**: `client/src-tauri/src/startup.rs::tests::writes_and_removes_run_value`
  - Given un registro falso When se activa y desactiva Then se escribe el comando con `pythonw.exe` y luego se borra.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `startup.rs` con la crate `windows`, comando Tauri y el interruptor de Ajustes > Sistema. Verify: `python -m devtools test-runner --type=tauri-check`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/settings/happy-start-at-login.e2e.ts` | toggle Start server with Windows on and off: the Tauri command is called with true and false | AC-8 |
