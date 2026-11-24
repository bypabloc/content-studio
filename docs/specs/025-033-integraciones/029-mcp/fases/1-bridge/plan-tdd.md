# Spec 029, fase 1: Bridge y herramientas

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `029-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-029/` o `tmp/spec-029/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: `studio mcp` responde las diez herramientas sobre el server compartido. **AC**: AC-1, AC-2, AC-3, AC-5, AC-11, AC-4, AC-8, AC-6, AC-7. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Lista cerrada de herramientas [AC-1]

- **RED**: `server/tests/unit/src/content_studio/mcp_server/test_tools.py::test_ac1_diez_herramientas_sin_admin`
  - WHEN se leen las definiciones THEN son las diez de 02 §2 con sus esquemas; el módulo no existe.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `mcp_server/tools.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/mcp_server -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Arranque bajo demanda [AC-2]

- **RED**: `server/tests/integration/test_mcp_bridge.py::test_ac2_primera_llamada_arranca_el_server`
  - Given una base temporal sin server When un cliente MCP en memoria llama `studio_capabilities` Then responde y `api.json` existe.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `mcp_server/bridge.py` con `ensure_running()`; `studio mcp` en `build_parser`. Verify: `uv run pytest server/tests/integration/test_mcp_bridge.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C3: Encolar, esperar y salidas [AC-3, AC-5, AC-11]

- **RED**: `server/tests/integration/test_mcp_bridge.py::test_ac3_narrate_y_wait_devuelven_rutas`
  - Given un servicio falso que escribe un `.wav` When se llama `studio_narrate` y `studio_wait_job` Then `outputs` trae la ruta y hay un `resource_link`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: herramientas de trabajo y la espera con eventos (o sondeo de `GET /jobs/{id}` cada segundo). Verify: `uv run pytest server/tests/integration/test_mcp_bridge.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C4: Entradas y validación [AC-4, AC-8]

- **RED**: `server/tests/unit/src/content_studio/mcp_server/test_tools.py::test_ac4_ruta_inexistente_da_input_not_found`
  - WHEN la ruta no existe THEN `isError` con `input_not_found`; con un `kind` inventado, los errores del 422.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: resolución de rutas y traducción de los 422. Verify: `uv run pytest server/tests -k "ac4 or ac8" -q`.
- **REFACTOR**: ninguno.

#### Ciclo C5: Cancelar y esperar la GPU [AC-6, AC-7]

- **RED**: `server/tests/integration/test_mcp_bridge.py::test_ac6_cancel_termina_el_proceso`
  - Given un trabajo falso de GPU y el candado tomado por otro pid When se consulta Then `waiting_gpu` y `waiting_on`; al cancelar, `cancelled`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: estado derivado del candado en `get_job`. Verify: `uv run pytest server/tests/integration/test_mcp_bridge.py -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
