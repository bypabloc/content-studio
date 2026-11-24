# Spec 027, fase 2: Tauri y Rust

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `027-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-027/` o `tmp/spec-027/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Crate de Tauri, plugins y crates en la última versión, edición 2024. **AC**: AC-1, AC-3, AC-4. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C2: Crate al día [AC-1, AC-3, AC-4]

- **RED**: `cargo test --manifest-path client/src-tauri/Cargo.toml`
  - Con las versiones nuevas escritas en `Cargo.toml` y antes de adaptar, `cargo test` falla donde cambió una API (se anota cuál en el commit).
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `cargo update`, versiones exactas, `cargo fix --edition` (D-3). Verify: `python -m devtools test-runner --type=tauri-check`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
