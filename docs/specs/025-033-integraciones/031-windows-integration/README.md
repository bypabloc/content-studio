# Spec 031: Windows: enlaces `content-studio://`, «Enviar a» e inicio con Windows

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `031-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-031/` o `tmp/spec-031/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Medium (6–10 archivos) |
| Rama | `feature/031-windows-integration` desde `origin/dev`, en `../content-studio-worktrees/031-windows-integration/` |
| Depende de | 030 (carpetas de entrada, que justifican el inicio con Windows) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Otra app o un script abre Content Studio en una sección, un trabajo o un formulario valores iniciales con un enlace `content-studio://`; desde el Explorador, «Enviar a» manda archivos a convertir, normalizar, limpiar o transcribir; y el server puede arrancar al iniciar sesión.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC | Primero |
| [02-diseno.md](02-diseno.md) | Flujo, formas de URL y argumentos, datos, módulos y textos | Antes de la primera fase |
| [fases/1-enlaces/](fases/1-enlaces/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-enviar-a/](fases/2-enviar-a/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [fases/3-inicio/](fases/3-inicio/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 3 | Al implementar la fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Enlaces `content-studio://`](fases/1-enlaces/plan-tdd.md) | C1, C2, C3 | AC-4, AC-5, AC-1, AC-2, AC-3 | - | IMP |
| F2 | [«Enviar a» desde el Explorador](fases/2-enviar-a/plan-tdd.md) | C4, C5 | AC-7, AC-6 | - | IMP |
| F3 | [Inicio con Windows](fases/3-inicio/plan-tdd.md) | C6 | AC-8 | - | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Esquema `content-studio://` con `tauri-plugin-deep-link` y `tauri-plugin-single-instance` (feature `deep-link`) (agente, 2026-11-24).
2. **D-2**: Un enlace nunca encola: navega o rellena, y el usuario confirma con el botón de la sección (agente, 2026-11-24).
3. **D-3**: «Enviar a» con accesos directos en la carpeta `SendTo` creados por el hook NSIS; el menú moderno de Windows 11 queda fuera (agente, 2026-11-24).
4. **D-4**: Inicio con Windows: valor `Run` de HKCU con `pythonw.exe -m content_studio api up`, apagado por defecto (agente, 2026-11-24).

## Reglas críticas

- La validación vive en una función pura con lista blanca; nada que venga de una URL llega a la API sin pasar por ella.
- Nunca se ejecuta una ruta recibida por URL: solo se muestra en el formulario si existe.
- Los plugins nuevos van con versión exacta (`frontend-stack.md`) y su ficha WARNING.
- Componentes según `ui-components.md`; textos en los tres catálogos.
- Cada archivo fuente en 300 líneas o menos.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C3 | `client/tests/unit/src/app/external/useExternalRequests.test.tsx` | e2e `happy-deeplink` |
| AC-2 | F1 | C3 | `client/tests/unit/src/app/external/useExternalRequests.test.tsx` | solo pytest |
| AC-3 | F1 | C3 | `client/tests/unit/src/app/external/useExternalRequests.test.tsx` | e2e `happy-deeplink` |
| AC-4 | F1 | C1 | `client/tests/unit/src/app/external/parseExternal.test.ts` | solo pytest |
| AC-5 | F1 | C2 | `client/src-tauri/src/external.rs::tests::forwards_argv_to_window` | 03 §2, paso 1 |
| AC-6 | F2 | C5 | `tests/e2e/app-check/031-sendto.check.ts` | `app-check run --binary=<instalador> --scenario=031-sendto` |
| AC-7 | F2 | C4 | `client/tests/unit/src/app/external/useExternalRequests.test.tsx (caso send)` | 03 §2, paso 2 |
| AC-8 | F3 | C6 | `client/src-tauri/src/startup.rs::tests::writes_and_removes_run_value` | `reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v ContentStudioServer` |

## WARNING y PENDING

- WARNING: `031-plugins-tauri` (dependencias nuevas), `031-enlaces-sin-efectos` (D-2), `031-sendto` (D-3).
- PENDING: `031-menu-moderno` en `docs/process/03-later/` si el usuario lo quiere después.
