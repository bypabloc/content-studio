# 020: la búsqueda en el contenido lee de disco, sin guardar texto en la base

- **Contexto**: la regla del usuario prohíbe guardar contenido en SQLite (solo rutas, metadatos y cachés numéricas). «Buscar también en el contenido» necesita el texto de los guiones (006) y las transcripciones (013 y el limpiador).
- **Elegida**: `library/text_search.py` lee, por ítem, el `script.json` (solo el texto de los segmentos), `transcript.json` y `words.json` de la carpeta de su trabajo y la transcripción en caché del archivo; normaliza espacios y mayúsculas y corta a los 2 s con lo que alcanzó. La búsqueda por nombre usa el nombre del archivo, no la carpeta del trabajo, cuyo nombre lleva parte del guion.
- **Descartadas**: una tabla FTS5 con el texto (rompe la regla de la base sin la decisión del usuario); leer también el `.txt` del limpiador (repite el `transcript.json`).
- **Límite de escala**: miles de ítems con JSON chicos responden en menos de un segundo en este equipo. Si una biblioteca grande pasa el límite de 2 s, la mejora es un índice FTS como caché regenerable: decidirlo con el usuario por la regla de la base.
- **Cómo revertir**: quitar `content` de `GET /library` y borrar `text_search.py`, esta ficha y su fila.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/library/test_text_search.py server/tests/unit/src/content_studio/db/test_schema.py`.
- **Pendiente**: ninguna.
