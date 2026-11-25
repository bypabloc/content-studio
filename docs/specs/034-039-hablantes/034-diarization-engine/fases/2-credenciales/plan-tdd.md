# Spec 034, fase 2: credenciales y API

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `034-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-034/` o `tmp/spec-034/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: guardar, consultar y borrar el token sin que la API lo devuelva, y negarse a instalar un motor restringido sin token. **AC**: AC-3, AC-4. **Depende de**: F1.

## Ciclos TDD

#### Ciclo C4: credenciales [AC-4]

- **RED**: `server/tests/unit/src/content_studio/api/routes/test_credentials.py::test_ac4_never_returns_the_token`
  - WHEN `PUT` con un token válido THEN `GET` devuelve `{"configured": true}` y el cuerpo no contiene el token. `GET /settings/secret.huggingface.token` y su `PUT` responden 403. `DELETE` deja `configured: false`. `"abc"` responde 422.
  - Doctest de `credentials.valid_token`.
- **GREEN**: `credentials.py`, `api/routes/credentials.py`, `api/routes/settings.py` y el registro de la ruta en `api/app.py`. Verify: `uv run pytest server/tests/unit/src/content_studio/api -q`.
- **REFACTOR**: ninguno.

#### Ciclo C5: instalar sin token [AC-3]

- **RED**: `server/tests/unit/src/content_studio/api/routes/test_engines.py::test_ac3_without_token_returns_409`
  - Given ningún token When `POST /engines/pyannote/install` Then 409 `error.engine_token_required` y la cola sigue vacía. Con token, 202 y un trabajo `engine.install`. `GET /engines` marca `gated: true`.
  - Un trabajo que sale con 25 termina con el código `engine_gated`.
- **GREEN**: `api/routes/engines.py` y el mapeo del exit code. Verify: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_engines.py -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: el flujo de UI está en la F3.
