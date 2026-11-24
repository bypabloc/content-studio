# 004: `starlette.testclient` avisa que httpx 0.28 está deprecado

- **Qué**: las pruebas de la API muestran un `DeprecationWarning` de httpx 0.28 al usar `starlette.testclient`.
- **Por qué no se hizo**: el aviso no rompe nada y la versión nueva depende de que starlette la soporte.
- **Cuándo**: cuando el proyecto migre a httpx2 o starlette publique soporte.
- **Quién**: agente.
- **Qué la cierra**: `uv run pytest server/tests/unit/src/content_studio/api` sin avisos de httpx.
