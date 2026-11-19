# 006: cada toma guarda sus bloques en `blocks/` y un `script.json` para regenerar sin el modelo

- **Contexto**: el estado del guion vive solo en memoria (`narration/pipeline.py`); al terminar el proceso no se puede regenerar un párrafo. El AC-2 pide que la carpeta de cada toma tenga `blocks/<i>.wav` y un `script.json` con una semilla por bloque.
- **Elegida**: cada bloque de voz (antes de sus pausas y de la velocidad del estilo) se escribe como WAV de 32 bits flotante en `blocks/<i>.wav`, y `script.json` guarda los segmentos, las referencias (`ref` y `text_ref`), la semilla de cada bloque, el idioma, el master y el LUFS. `write_blocks` y `write_script` se llaman desde `regenerate()`, en la carpeta del `.wav` de la toma, así el disco siempre refleja la memoria. La regeneración (grupo 4) copia los bloques que no cambian como archivo, para que su hash sea el mismo.
- **Descartadas**: guardar solo el texto y regenerar la toma completa (cambiaría todos los bloques y no cumpliría el AC-3); guardar un pickle de `g` (no es legible ni versionable, y ata el formato a Python); PCM de 24 bits en los bloques (cuantiza otra vez lo que ya salió del modelo).
- **Cómo revertir**: quitar `write_blocks` y `write_script` de `pipeline.py` y sus dos llamadas en `regenerate()`; la toma final no cambia.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/narration/test_pipeline.py` (AC-2) y, en la verificación final (T9), `sha1sum` de `blocks/0.wav` y `blocks/2.wav` de las dos tomas.
- **Pendiente**: [`006-cli-carpeta-compartida`](../PENDING/006-cli-carpeta-compartida.md): con `--output archivo.wav`, dos tomas en la misma carpeta comparten `blocks/` y `script.json`.
- **Antes de**: el merge a `dev`.
