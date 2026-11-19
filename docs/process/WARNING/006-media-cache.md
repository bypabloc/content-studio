# 006: la caché de medios va en memoria, no en la tabla `media_cache` de D-3

- **Contexto**: D-3 pide guardar la duración, el LUFS y el pico en una tabla `media_cache` (migración 2). La migración 2 también agrega `jobs.starred` y `jobs.group_key` (D-4), y el AC-4 solo pide que los números sean correctos. Medir un audio de narración tarda segundos, y la UI pide la información una vez por resultado.
- **Elegida**: un diccionario en memoria en `api/routes/media.py`, con clave (ruta, `mtime_ns`, tamaño), igual que la clave que pide el plan. La migración 2 queda con lo que dice D-4.
- **Descartadas**: la tabla `media_cache` (una migración más sin un AC que la pida, y los números se recalculan al reiniciar el server, que es barato); no cachear (cada render de la UI volvería a correr ffmpeg).
- **Cómo revertir**: si un guion muy largo hace lenta la primera consulta, o si los números deben sobrevivir a reiniciar, crear la tabla en la migración 2 y leer de ella en `media_info`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_media.py` (AC-4); la caché no se prueba aparte porque la clave cambia con el archivo.
- **Antes de**: el merge a `dev`.
