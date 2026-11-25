# 025: el venv del server se recrea en una carpeta vacía al cambiar de Python

- **Contexto**: el instalador (spec 022) reutilizaba el venv del server mientras la versión de la app no cambiara. Con Python 3.15 hay que recrearlo cuando cambia la Python (D-5). El marcador `venv/.app-version` vive dentro de la carpeta del venv.
- **Elegida**: `clear_venv` borra el venv y deja la carpeta vacía; `uv sync --python 3.15` la llena. El marcador nuevo `venv/.python-installed` guarda la versión con la que se creó y se escribe solo tras una sincronización correcta.
- **Descartadas**: borrar la carpeta sin recrearla (los marcadores no se podrían escribir si un paso falla a medias); recrear sin borrar (uv recrea el venv solo cuando la Python difiere, pero el borrado explícito es determinista y es lo que pide la spec).
- **Cómo revertir**: quitar `clear_venv`, `python_marker` y su uso en `prepare` (commit de la fase 3).
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml prepare` (cinco pruebas, incluida `recreates_venv_when_python_changes`). Antes de `main`: la app instalada sobre una instalación previa con 3.12 (03 §2, punto 4; AC-6).
- **Pendiente**: la prueba con el instalador real queda en la verificación final; si no se puede correr, ficha en `PENDING/`.
