# 030: la pausa es un POST con `paused`, y reanudar usa el mismo camino

- **Contexto**: 02 §2 lista `POST /inbox/folders/{id}/pause` sin cuerpo, pero la interfaz necesita pausar y también reanudar.
- **Elegida**: el cuerpo `{"paused": true}` o `{"paused": false}`; `{}` pausa, porque `paused` vale `true` por defecto. Una sola ruta para los dos sentidos.
- **Descartadas**: `pause` y `resume` como dos rutas (una más que mantener); `PATCH` de la carpeta (la carpeta tiene más campos y aquí solo cambia la pausa).
- **Cómo revertir**: quitar `PauseIn` y separar en dos rutas en `api/routes/inbox.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_inbox.py`.
