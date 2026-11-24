# Spec 031, fase 2: «Enviar a» desde el Explorador

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `031-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-031/` o `tmp/spec-031/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Encolar archivos desde el menú del Explorador. **AC**: AC-7, AC-6. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C4: `--send` a trabajos [AC-7]

- **RED**: `client/tests/unit/src/app/external/useExternalRequests.test.tsx (caso send)`
  - WHEN llega `--send convert-mp3 a.wav b.wav no.wav` THEN dos `POST /jobs` y el aviso con 2 y 1 saltado.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: acciones de `--send` en `parseExternal` y su despacho. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

#### Ciclo C5: Accesos directos del instalador [AC-6]

- **RED**: `tests/e2e/app-check/031-sendto.check.ts`
  - WHEN `app-check` instala la app aislada THEN los cinco `.lnk` existen y, al desinstalar, no.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `hooks.nsh` con `CreateShortCut` en `$APPDATA\Microsoft\Windows\SendTo` y su borrado. Verify: `python -m devtools app-check run --binary=<exe> --scenario=031-sendto`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
