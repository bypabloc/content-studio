# Spec 032, fase 3: Firewall y Ajustes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `032-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-032/` o `tmp/spec-032/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Activar, emparejar y revocar desde la app. **AC**: AC-9, AC-10. **Depende de**: fase 2.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C7: Regla de firewall [AC-9]

- **RED**: `client/src-tauri/src/firewall.rs::tests::builds_private_profile_rule`
  - WHEN se pide la regla THEN el comando de `netsh` lleva `profile=private` y el puerto; si `ShellExecuteW` devuelve cancelado, `firewall_declined`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `firewall.rs` y su comando Tauri. Verify: `python -m devtools test-runner --type=tauri-check`.
- **REFACTOR**: ninguno.

#### Ciclo C8: Red local en Integraciones [AC-10]

- **RED**: `client/tests/unit/src/features/settings/LanPanel.test.tsx`
  - WHEN se pulsa «Emparejar dispositivo» THEN se ve el PIN con su cuenta regresiva; «Revocar» pide confirmación.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `LanPanel.tsx` con átomos y moléculas y claves de 02 §5. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/settings/happy-lan-pairing.e2e.ts` | enable LAN (mock firewall ok), pick an address, pair a device, see it listed, revoke it accepting the confirm | AC-10 |
| `tests/e2e/settings/neg-lan-firewall-declined.e2e.ts` | the firewall command returns declined: the panel shows the message and LAN stays off | AC-9, AC-10 |
