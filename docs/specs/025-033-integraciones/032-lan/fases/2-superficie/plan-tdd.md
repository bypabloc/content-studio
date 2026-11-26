# Spec 032, fase 2: Rutas remotas, subidas y MCP por HTTP

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `032-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-032/` o `tmp/spec-032/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Lo que un dispositivo puede hacer, y nada más. **AC**: AC-5, AC-6, AC-8. **Depende de**: fase 1.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C4: Lista cerrada de rutas [AC-5]

- **RED**: `server/tests/unit/src/content_studio/api/test_app.py::test_ac5_remote_without_admin_routes`
  - WHEN se arma `create_app(remote=True)` THEN sus rutas son exactamente las de 02 §2.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: parámetro `remote` en `create_app`. Verify: `uv run pytest server/tests/unit/src/content_studio/api -q`.
- **REFACTOR**: ninguno.

#### Ciclo C5: Subidas y guarda de parámetros [AC-6]

- **RED**: `server/tests/unit/src/content_studio/lan/test_guard.py::test_ac6_upload_yes_path_no`
  - WHEN `params` trae `C:/Users/x/a.wav` THEN `remote_path_not_allowed`; con `upload:3`, la ruta de la subida; un `kind` de motores, `kind_not_allowed_remote`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `lan/guard.py`, `POST /uploads` con tope. Verify: `uv run pytest server/tests -k "guard or uploads" -q`.
- **REFACTOR**: ninguno.

#### Ciclo C6: MCP por Streamable HTTP [AC-8]

- **RED**: `server/tests/integration/test_lan.py::test_ac8_mcp_http_lists_and_checks_origin`
  - WHEN un cliente MCP HTTP del SDK se conecta con el token del dispositivo THEN lista las herramientas sin `studio_watch_folder`; con `Origin: https://evil.example`, 403.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: montar la app HTTP del SDK en `/mcp` (con su `lifespan`) usando `mcp_server/tools.py`. Verify: `uv run pytest server/tests/integration/test_lan.py -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
