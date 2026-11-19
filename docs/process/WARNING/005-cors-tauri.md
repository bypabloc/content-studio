# 005: la API acepta solo los orígenes de la ventana de Tauri (CORS)

- **Contexto**: la ventana de Tauri pide a `http://127.0.0.1:<puerto>` desde su propio origen (`http://tauri.localhost` en Windows, `tauri://localhost` en macOS y Linux). Sin cabeceras CORS, el navegador de la ventana bloquea cada `fetch` y el `EventSource` de `/events`, y la app no cargaría ningún dato. Los e2e no lo vieron porque mockean la API.
- **Elegida**: `CORSMiddleware` con una lista cerrada de orígenes (`TAURI_ORIGINS` en `server/src/content_studio/api/app.py`): los dos de Tauri y el dev server de Vite (`localhost:1420`). Las cabeceras permitidas son `authorization` y `content-type`. El token sigue siendo la barrera real: CORS solo deja que la ventana lo use.
- **Descartadas**: `allow_origins=['*']` (cualquier web abierta en el navegador podría llamar a la API local); un proxy en Rust (más código y otro punto de fallo).
- **Cómo revertir**: quitar `app.add_middleware(CORSMiddleware, ...)` de `create_app`. La app dejará de cargar datos en la ventana.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/test_app.py` (preflight del origen de Tauri y rechazo de otro origen), y la app real con `bun run --cwd client tauri dev` cargando la cola.
