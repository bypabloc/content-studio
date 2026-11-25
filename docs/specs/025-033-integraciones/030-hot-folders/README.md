# Spec 030: Carpetas de entrada: soltar un archivo y recibir el resultado

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `030-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-030/` o `tmp/spec-030/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/030-hot-folders` desde `origin/dev`, en `../content-studio-worktrees/030-hot-folders/` |
| Depende de | 029 (lista de herramientas MCP) y 028 (`IdleClock`) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Una app que solo sabe escribir archivos (un editor, un grabador, un script) suelta un medio o un `.job.json` en una carpeta que eligió el cliente, y recibe el resultado en su subcarpeta `done/` con un recibo JSON.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC, debe sonar | Primero |
| [02-diseno.md](02-diseno.md) | Flujo, API, CLI y MCP, tablas, módulos y textos | Antes de la primera fase |
| [fases/1-nucleo/](fases/1-nucleo/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-superficies/](fases/2-superficies/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, escucha, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Tablas, sondeo y recibos](fases/1-nucleo/plan-tdd.md) | C1, C2, C3, C4, C5 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 | - | IMP |
| F2 | [API, CLI, MCP y Ajustes](fases/2-superficies/plan-tdd.md) | C6, C7 | AC-1, AC-10, AC-9 | 33576cf | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | IMP |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: La carpeta la indica el cliente (app, API, CLI o MCP), con una operación y sus parámetros por carpeta (usuario, 2026-11-24).
2. **D-2**: Sondeo con stdlib cada 2 s; un archivo está listo cuando su tamaño y su fecha no cambian en dos sondeos (agente, 2026-11-24).
3. **D-3**: Resultados dentro de la carpeta: `processing/`, `done/<nombre>/` con el original, las salidas y `<nombre>.result.json`, y `failed/<nombre>/` con `<nombre>.error.json` (agente, 2026-11-24).
4. **D-4**: Una carpeta con `keep_awake` (por defecto sí) mantiene el server encendido; sin él, lo que se suelte con el server apagado se procesa la próxima vez que arranque (agente, 2026-11-24).
5. **D-5**: `studio_watch_folder` se suma como herramienta MCP número 11 (agente, 2026-11-24).

## Reglas críticas

- Nunca se borra un archivo del usuario: el original se mueve a `processing/` y después a `done/` o `failed/` dentro de su misma carpeta.
- La carpeta registrada debe existir; sus subcarpetas las crea la app.
- `inbox/` solo importa stdlib.
- Migración SQL que solo agrega; SQLite guarda rutas, no contenido.
- Textos visibles en los tres catálogos.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/unit/src/content_studio/inbox/test_store.py::test_ac1_registers_a_valid_folder_and_rejects_the_rest` | solo pytest |
| AC-1 | F2 | C6 | `server/tests/unit/src/content_studio/api/routes/test_inbox.py::test_ac1_post_get_pause_delete` | solo pytest |
| AC-2 | F1 | C2 | `server/tests/unit/src/content_studio/inbox/test_scanner.py::test_ac2_takes_a_file_once_it_is_stable_across_two_sweeps` | solo pytest |
| AC-3 | F1 | C2 | `server/tests/unit/src/content_studio/inbox/test_scanner.py::test_ac3_skips_partial_temporary_and_growing_files` | solo pytest |
| AC-4 | F1 | C3 | `server/tests/unit/src/content_studio/inbox/test_receipts.py::test_ac4_done_keeps_the_original_outputs_and_a_result_receipt` | 03 §2, paso 1 |
| AC-5 | F1 | C3 | `server/tests/unit/src/content_studio/inbox/test_receipts.py::test_ac5_failed_keeps_the_original_and_an_error_receipt` | solo pytest |
| AC-6 | F1 | C4 | `server/tests/unit/src/content_studio/inbox/test_scanner.py::test_ac6_job_file_with_relative_paths_is_queued_or_failed` | solo pytest |
| AC-7 | F1 | C5 | `server/tests/integration/test_inbox.py::test_ac7_does_not_reprocess_after_a_restart` | solo pytest |
| AC-8 | F1 | C5 | `server/tests/integration/test_inbox.py::test_ac8_keep_awake_holds_the_server_until_released` | solo pytest |
| AC-9 | F2 | C7 | `client/tests/unit/src/features/settings/InboxFolders.test.tsx` | e2e `happy-inbox-folders` |
| AC-10 | F2 | C6 | `server/tests/unit/src/content_studio/mcp_server/test_bridge.py::test_ac10_watch_folder_registers_the_folder_through_the_api` | solo pytest |
| AC-10 | F2 | C6 | `server/tests/unit/src/content_studio/mcp_server/test_catalog.py::test_ac1_eleven_tools_with_schemas_and_no_admin` | solo pytest |

## WARNING y PENDING

- WARNING: `030-sondeo-stdlib` (D-2), `030-keep-awake` (D-4), `030-recibos-por-sondeo`, `030-cancelado-como-fallo`, `030-validacion-al-registrar`, `030-codigos-propios-del-inbox`, `030-pausa-por-cuerpo`, `030-mcp-por-api`.
- PENDING: `030-unidades-de-red` si no se pudo probar en OneDrive o en una unidad de red; `030-recibo-mensaje-locale`, `030-ajustes-mas-operaciones`, `030-axe-language-intermitente`, `030-unidades-de-red`, `030-appcheck-peaks-403`.
