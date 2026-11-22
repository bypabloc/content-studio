# 024: `/media/peaks` responde 403 para las muestras del catálogo de voces

- **Qué**: la primera corrida de `app-check` (22-11-2026) registró en `http_4xx` 8 respuestas `403 GET /media/peaks?path=server/data/narration/voices/karen-savage/<estilo>.wav&n=2000` al abrir el catálogo. Las ondas de esas muestras no se dibujan. La CSP también bloquea el IPC por `ipc.localhost` (`connect-src`), y Tauri cae a `postMessage` (`WARNING/024-dialogo-por-webview`).
- **Por qué no se hizo**: es un defecto de la ruta `/media/peaks` o de sus raíces permitidas, no de la 024.
- **Cuándo**: con la próxima spec que toque voces o `/media`.
- **Quién**: agente.
- **Qué la cierra**: un test de regresión en `server/tests/integration/test_bugs.py` y `python -m devtools app-check run` sin esos 403 en `http_4xx`.
