# Spec 029, fase 2: Configuración por cliente

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `029-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-029/` o `tmp/spec-029/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Copiar la configuración de cada cliente desde el CLI o la app. **AC**: AC-9, AC-10. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C6: `studio mcp config` [AC-9]

- **RED**: `server/tests/unit/src/content_studio/mcp_server/test_config.py::test_ac9_fragmento_valido_por_cliente`
  - WHEN se pide cada cliente THEN el fragmento se parsea (JSON o TOML con `tomllib` en el test) y trae el comando de `studio mcp`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `mcp_server/config.py` y `GET /integrations/mcp-config`. Verify: `uv run pytest server/tests/unit/src/content_studio/mcp_server -q`.
- **REFACTOR**: ninguno.

#### Ciclo C7: Copiar desde Integraciones [AC-10]

- **RED**: `client/tests/unit/src/features/settings/McpConfig.test.tsx`
  - WHEN se elige Codex THEN el botón copia el fragmento de la API.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: molécula en el panel de la 028 y claves de 02 §5. Verify: `bun run --cwd client test`.
- **REFACTOR**: ninguno.

## Matriz e2e

| Archivo | Recorre | AC |
| :--- | :--- | :--- |
| `tests/e2e/settings/happy-mcp-config.e2e.ts` | open Settings > Integrations, pick Claude Code, copy the config, check the clipboard text | AC-10 |
| `tests/e2e/settings/neg-mcp-config-error.e2e.ts` | the mock API fails: the panel shows the catalog error and no copy button | AC-10 |
