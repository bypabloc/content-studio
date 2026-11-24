# 020: el índice inicial corre al abrir la base, no dentro de la migración 7

- **Contexto**: la spec pide indexar en la migración los trabajos `done` anteriores, pero las migraciones son SQL puro y listar los archivos de cada carpeta y medir su duración exige Python y ffprobe.
- **Elegida**: la migración 7 crea las tablas; `library.index.backfill` recorre los `done` una sola vez y deja el setting `library.backfilled`. Lo llaman `create_app` (la app y `serve`) y el CLI `studio library`.
- **Descartadas**: un hook de Python dentro de `schema.migrate` (mezcla datos de disco con la migración, que también corre en bases en memoria y en tests); indexar en cada `GET /library` (repite el recorrido).
- **Cómo revertir**: quitar la llamada a `backfill` de `api/app.py` y `cli/library.py`, y borrar esta ficha y su fila.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/library/test_index.py -k backfill`.
- **Pendiente**: ninguna.
