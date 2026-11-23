# 018: decodificación alfa y caché de fotogramas

- **Contexto**: el decodificador predeterminado de FFmpeg descartó el canal alfa de una fuente VP9 al escalarla para el proxy. La caché de fotogramas tampoco quedaba invalidada si cambiaba un medio sin cambiar `project.json`.
- **Elegida**: usar `libvpx-vp9` para decodificar la fuente VP9 con `alpha_mode`, codificar el proxy WebM en `yuva420p` y calcular la clave del fotograma con la revisión del proyecto y el mtime/tamaño de cada fuente visual.
- **Descartadas**: el decodificador predeterminado, que producía un proxy opaco; una clave que solo usara el JSON, que podía servir un fotograma viejo.
- **Cómo revertir**: retirar el decodificador explícito y la firma de fuentes en `editor/proxy.py` y `api/routes/editor.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/editor/test_proxy.py server/tests/unit/src/content_studio/api/routes/test_editor_frame.py -q` con FFmpeg y ffprobe disponibles.
- **Pendiente**: ninguna.
