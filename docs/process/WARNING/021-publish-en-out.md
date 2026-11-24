# 021: publish.json en la carpeta del trabajo

- **Contexto**: la spec pide guardar `publish.json` «junto al archivo» y su ruta en `library_items.publish_path`. Un ítem de una carpeta vigilada vive en una carpeta del usuario.
- **Elegida**: `publish.json` queda en la carpeta del trabajo `llm.publish` (`out/llm/<fecha>-<id>-.../publish.json`) y la base guarda solo esa ruta (migración 8, porque la 7 ya la usó la 020). `GET /library/{id}/publish` lo lee de ahí.
- **Descartadas**: escribirlo al lado del video (crearía archivos en las carpetas vigiladas del usuario, que la app solo lee); guardar el JSON en la base (la base solo guarda metadatos, `test_no_blob_columns`).
- **Cómo revertir**: en `llm/tasks/publish.py::finish`, cambiar `out_dir` por `Path(params['source']).parent`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/llm/tasks/test_publish.py`.
- **Pendiente**: ninguna.
