# 023: Publicar busca la transcripción por la ruta literal

- **Qué**: `llm.publish` busca en `transcripts` con `source_path = <ruta del ítem>` tal cual. La misma ruta escrita con `/` o con otra mayúscula de unidad no coincide, y un trabajo `transcribe` suelto no guarda en esa tabla (solo Limpiar, Subtítulos y Mezcla), así que el aviso «no tiene transcripción» aparece aunque la haya.
- **Por qué no se hizo**: fuera del alcance de la 023: en la app, la ruta sale de la biblioteca y coincide; el aviso dice qué hacer.
- **Cuándo**: después del lote.
- **Quién**: agente.
- **Qué la cierra**: comparar rutas resueltas (`Path.resolve()`, sin distinguir mayúsculas en Windows) en `transcription/cache.py` y en `publish.prepare`, con una prueba.
