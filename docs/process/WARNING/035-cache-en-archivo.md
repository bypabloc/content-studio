# 035: caché de diarización en archivo, sin tabla ni migración

- **Contexto**: el diseño pedía una tabla `diarizations` con su migración. `job_main` corre en el Python del server y no recibe la ruta de la base; quien busca la caché es ese proceso.
- **Elegida**: el resultado en `<datos>/diarizations/<sha1>.json`, con la clave de ruta, mtime, tamaño y hablantes pedidos (AC-8). Sin tabla ni migración: nadie consulta un índice.
- **Descartadas**: la tabla con migración, que obligaba a abrir la base desde el proceso de la cola sin aportar nada que la clave del archivo no dé; una caché dentro de la carpeta del trabajo (no se reusaría entre trabajos).
- **Cómo revertir**: añadir la tabla `diarizations` al final de `MIGRATIONS` en `server/src/content_studio/db/schema.py` y consultarla antes del archivo en `diarization/cache.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/diarization/test_cache.py -q`.
- **Pendiente**: ninguno.
