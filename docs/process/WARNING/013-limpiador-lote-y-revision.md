# 013: Limpiador: lote, auto_render, `studio clean` y revisión sobre la onda

- **Contexto**: la spec pide `auto_render` (D-4), `studio clean <archivos> [--auto]` (T6) y la revisión con regiones, línea de tiempo y transcripción (D-6). El worker no encadenaba trabajos, `GET /engines` no traía los modelos de whisper y el nombre de las salidas no lo fija la spec.
- **Elegida**:
  - `auto_render`: al terminar un `clean.analyze` con esa bandera, `Worker._chain` encola `clean.render` con su carpeta. La API y la app lo usan igual.
  - `studio clean` no espera al worker: analiza con `submit.execute` y, con `--auto`, renderiza con `submit.run` sobre la carpeta que devuelve. No hace falta `studio serve` para terminar.
  - Salidas del render: `clean.wav` y `clean.mp4` (antes `limpio.*`). Los demás archivos del análisis ya tienen nombres en inglés (`transcript.txt`, `cuts.edl`).
  - `GET /engines` suma `models` solo a `faster-whisper`: tamaño, VRAM, recomendado y `downloaded` (existe un `model.bin` en `hf/models--<repo>/snapshots/*`).
  - Revisión: WaveSurfer 8 con los plugins Regions, Timeline y Zoom sobre el mismo `<video>` o `<audio>` (opción `media`). La onda sigue la reproducción sin sincronía manual. `useSyncedMedia` solo lleva el tiempo, la reproducción y la vista previa que salta cortes.
  - `/plan` se llama con cada cambio de hueco, margen o bordes. Solo cuenta la última respuesta (`planned`), así que una respuesta vieja no pisa los cortes.
  - `UIRecommendedSelect`: la opción recomendada muestra «Recomendado · pista». Antes la pista (tamaño y descarga) se perdía detrás del ★.
  - Idiomas: `es` ★ por defecto, luego `en`, `pt`, `fr`, `de`, `it` y `auto` (Detectar).
  - Diccionario de cspell: `nvenc` en los términos del proyecto; `deutsch` y `français` por archivo de catálogo (nombres de idioma).
- **Descartadas**:
  - Encadenar el render de `studio clean` por el worker: obligaría a dejar `studio serve` corriendo.
  - Un `<video>` aparte para la onda: duplica la sincronía que WaveSurfer ya hace con `media`.
  - Conservar `limpio.*`: mezcla idiomas en los nombres de archivo y cspell los marcaba.
- **Cómo revertir**: quitar `services/clean_*`, `api/routes/clean.py`, `features/cleaner/`, `_chain` del worker y el subcomando `clean` de `cli/main.py`. Las claves `cleaner.*`, `whisper.*` y `nav.*` salen de los tres catálogos.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/{cli,jobs,clean,services,api,transcription}`; en `client/`, `bun x vitest run tests/unit/src/features/cleaner`; `uv run studio clean --help` y `uv run studio clean no-existe.mp4` (sale con 2 y el mensaje del catálogo).
- **Pendiente**: la corrida real con video de 3 a 5 minutos y large-v3-turbo (AC-11), la medición de VRAM y la escucha del usuario: `docs/specs/001-017-studio/013-whisper-cleaner/03-verificacion-final.md` (borrada por la 023; en el historial de git).
