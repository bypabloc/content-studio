# 004: cancelar termina el árbol del proceso (taskkill en Windows, grupo en POSIX)

- **Contexto**: `Popen.terminate()` no alcanza a los hijos del motor (ffmpeg, el Python del venv). Un trabajo cancelado podía dejar el modelo cargado en la GPU.
- **Elegida**: Windows con `taskkill /T /F`; POSIX con SIGTERM al grupo y SIGKILL si no sale en 5 s (`stop_tree` en `server/src/content_studio/jobs/worker.py`). Cancelar desde otro proceso (`studio jobs cancel`) termina el trabajo en menos de 0,5 s.
- **Descartadas**: `terminate()` (no mata hijos); solo SIGKILL (no deja limpiar el archivo parcial).
- **Cómo revertir**: volver a `Popen.terminate()` en `stop_tree` (cambio de `b99bff7`).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/jobs` (rama de Windows). La rama POSIX no se ejecuta en Windows.
- **Antes de `main`**: en WSL, cancelar un trabajo real y comprobar que no queda `ffmpeg` ni Python huérfanos.
