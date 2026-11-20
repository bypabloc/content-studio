# 007: el id de trabajo en la ruta es entero, así que `/jobs/nope` responde 422 y no `job_not_found`

- **Contexto**: el AC-2 de la 007 pide `GET /jobs/nope` con `job_not_found`, pero `get_job` tipa `job_id` como `JobId` (entero). FastAPI rechaza `nope` con su propio 422 antes de llegar a la app, y ese error no pasa por `_http_error`.
- **Elegida**: las pruebas de idioma (`api/test_errors_locale.py`) usan `/jobs/999`, un id numérico que no existe. Cubren lo que el AC quiere: el error de dominio sale en el idioma de `Accept-Language`.
- **Descartadas**: cambiar `JobId` a texto (cambia el contrato OpenAPI de la 004 y los tipos del client generados); traducir los 422 de validación en esta spec (fuera de alcance, va a PENDING).
- **Cómo revertir**: no aplica; no hay cambio de código, solo la elección del id en las pruebas.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/test_errors_locale.py -q` pasa, y `GET /jobs/nope` devuelve el 422 de FastAPI.
- **Pendiente**: [PENDING 007-errores-validacion](../PENDING/007-errores-validacion.md).
- **Antes de**: el merge a `dev`.
