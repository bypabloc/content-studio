# 028: el apagado pasa por `POST /server/stop` y los guards se montan en `serve`

- **Contexto**: `studio api down` tiene que detener el server sin dejar el lock ni `api.json` a medias, y solo cuando no hay trabajos (AC-6). El guard de Host (AC-10) y el de actividad (AC-5) deben ver el tráfico real.
- **Elegida**: `down` pide el apagado con `POST /server/stop` (con token) y `serve` lo atiende, borra `api.json` y suelta el lock. Los guards `HostGuard` (400 `host_not_allowed`) y `ActivityGuard` (marca uso salvo `/health` y `/events`) se montan en `serve`, no en `create_app`.
- **Descartadas**: matar el pid con `os.kill` o `taskkill` (no limpia el lock ni `api.json`; no sirve para esperar trabajos); montar los guards en `create_app` (los tests de la API usan `TestClient` con Host `testserver` y se romperían).
- **Cómo revertir**: quitar la ruta `server_control` y los guards de `serve._run`; `down` volvería a no tener cómo parar el server.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/test_guards.py server/tests/unit/src/content_studio/api/routes/test_server_control.py`.
