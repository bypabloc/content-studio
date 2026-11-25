# Spec 029: Servidor MCP local (`studio mcp`) para LLMs y agentes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `029-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-029/` o `tmp/spec-029/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/029-mcp` desde `origin/dev`, en `../content-studio-worktrees/029-mcp/` |
| Depende de | 028 (server compartido y `runtime/`) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Claude Code, Codex, VS Code, Cursor, Claude Desktop, LM Studio, Jan o AnythingLLM pueden pedirle a content-studio que narre, componga música, transcriba, limpie o convierta, esperar el resultado y recibir la ruta del archivo, sin abrir la app.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC, debe sonar | Primero |
| [02-diseno.md](02-diseno.md) | Flujo, las 10 herramientas, CLI, módulos y textos | Antes de la primera fase |
| [fases/1-bridge/](fases/1-bridge/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-configuracion/](fases/2-configuracion/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, escucha, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Bridge y herramientas](fases/1-bridge/plan-tdd.md) | C1, C2, C3, C4, C5 | AC-1, AC-2, AC-3, AC-5, AC-11, AC-4, AC-8, AC-6, AC-7 | - | IMP |
| F2 | [Configuración por cliente](fases/2-configuracion/plan-tdd.md) | C6, C7 | AC-9, AC-10 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Transporte stdio con el SDK oficial `mcp` (última versión); el HTTP queda para la LAN (032) (agente, 2026-11-24).
2. **D-2**: Diez herramientas `studio_*` por tarea más una genérica `studio_submit_job` (usuario delegó, agente, 2026-11-24).
3. **D-3**: Trabajos largos con `studio_wait_job` (hasta 300 s, con progreso) y `studio_get_job`; sin depender de la extensión *tasks* (agente, 2026-11-24).
4. **D-4**: Salidas como ruta y `resource_link` `file:///`, nunca base64 (agente, 2026-11-24).
5. **D-5**: Entradas: cualquier archivo existente del sistema, resuelto y sin seguir a carpetas que no existen (usuario, 2026-11-24).
6. **D-6**: Nada administrativo en el MCP (motores, almacenamiento, ajustes, `/fs`, papelera) (agente, 2026-11-24).

## Reglas críticas

- `cli/` sigue con solo stdlib: `studio mcp` importa `mcp_server` dentro de su función, y el SDK se importa dentro de `bridge.run_stdio`.
- El token no se escribe en la salida de `studio mcp config` ni en ningún log: el bridge lo lee del archivo.
- Una herramienta nueva necesita su caso en el test de AC-1 (la lista es cerrada).
- Descripciones de las herramientas en inglés (son para el modelo); los errores, del catálogo.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/integration/test_mcp_bridge.py::test_ac1_protocol_lists_ten_tools` y `server/tests/unit/src/content_studio/mcp_server/test_catalog.py::test_ac1_ten_tools_with_schemas_and_no_admin` | solo pytest |
| AC-2 | F1 | C2 | `server/tests/integration/test_mcp_bridge.py::test_ac2_first_call_starts_the_server` | solo pytest |
| AC-3 | F1 | C3 | `server/tests/integration/test_mcp_bridge.py::test_ac3_narrate_and_wait_return_paths_over_protocol` | 03 §2 |
| AC-4 | F1 | C4 | `server/tests/unit/src/content_studio/mcp_server/test_tools.py::test_ac4_missing_input_path_gives_input_not_found` y `test_bridge.py::test_ac4_missing_input_path_is_error_and_not_queued` | solo pytest |
| AC-5 | F1 | C3 | `server/tests/integration/test_mcp_bridge.py::test_ac5_wait_reports_progress_and_times_out_without_error` | 03 §2 |
| AC-6 | F1 | C5 | `server/tests/integration/test_mcp_bridge.py::test_ac6_cancel_ends_the_process` | solo pytest |
| AC-7 | F1 | C5 | `server/tests/integration/test_mcp_bridge.py::test_ac7_gpu_queued_says_who_holds_it` | solo pytest |
| AC-8 | F1 | C4 | `server/tests/unit/src/content_studio/mcp_server/test_bridge.py::test_ac8_invalid_params_return_service_errors` | solo pytest |
| AC-9 | F2 | C6 | `server/tests/unit/src/content_studio/mcp_server/test_config.py::test_ac9_fragmento_valido_por_cliente` | solo pytest |
| AC-10 | F2 | C7 | `client/tests/unit/src/features/settings/McpConfig.test.tsx` | e2e `happy-mcp-config` |
| AC-11 | F1 | C3 | (sin pytest: verificación final) | 03 §2, pasos 1 y 2 |

## WARNING y PENDING

- WARNING: `029-sdk-mcp` (dependencia nueva, `stack.md` §5), `029-herramientas` (D-2).
- PENDING: `029-clientes-sin-probar` con los clientes de la tabla que no se pudieron probar de verdad.
