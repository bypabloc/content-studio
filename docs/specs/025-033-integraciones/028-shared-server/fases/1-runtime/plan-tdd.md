# Spec 028, fase 1: Runtime del server

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `028-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-028/` o `tmp/spec-028/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Descubrimiento, token, instancia única, inactividad y `studio api`. **AC**: AC-4, AC-1, AC-2, AC-3, AC-6, AC-5, AC-10. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Descubrimiento y token [AC-4]

- **RED**: `server/tests/unit/src/content_studio/runtime/test_discovery.py::test_ac4_token_persiste_y_rota`
  - WHEN se pide el token dos veces THEN es el mismo; con `rotate=True`, otro; el módulo no existe.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `runtime/discovery.py` con escritura atómica. Verify: `uv run pytest server/tests/unit/src/content_studio/runtime -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Instancia única y `studio api` [AC-1, AC-2, AC-3, AC-6]

- **RED**: `server/tests/integration/test_shared_server.py::test_ac2_dos_up_un_server`
  - WHEN dos `ensure_running` corren a la vez sobre una base temporal THEN hay un solo pid; hoy no existe `ensure_running`.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `runtime/instance.py`, `cli/api.py` y la línea en `build_parser`. Verify: `uv run pytest server/tests/integration/test_shared_server.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C3: Apagado por inactividad [AC-5]

- **RED**: `server/tests/unit/src/content_studio/runtime/test_idle.py::test_ac5_sale_sin_uso_y_no_con_trabajos`
  - Given un reloj falso When pasan los minutos sin `touch` y sin trabajos Then `idle()` es True; con un trabajo `running`, False.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `runtime/idle.py` y el hilo de `serve.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/runtime -q`.
- **REFACTOR**: ninguno.

#### Ciclo C4: Guarda de Host [AC-10]

- **RED**: `server/tests/unit/src/content_studio/api/test_app.py::test_ac10_host_ajeno_da_400`
  - WHEN el cliente manda `Host: evil.example` THEN 400 `host_not_allowed`; hoy 200.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `TrustedHostMiddleware` y el código en los catálogos. Verify: `uv run pytest server/tests/unit/src/content_studio/api -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
