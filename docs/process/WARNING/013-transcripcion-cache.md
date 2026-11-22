# 013: transcripción con faster-whisper, caché en disco y la migración 4

- **Contexto**: la spec pide la migración 3 para la caché, pero la 3 ya la usan `starred` y `group_key` (spec 006). Además, `engines/recipes.py` solo admite las familias `narration`, `music` y `system`.
- **Elegida**:
  - La tabla `transcripts` es la migración 4 (`PRAGMA user_version = 4`); guarda ruta, mtime, tamaño, modelo, idioma y la ruta del JSON, y ninguna columna BLOB ni de texto.
  - La familia `transcription` se suma a las de recetas, para la receta `faster-whisper.json`.
  - Clave de la caché: sha1 de ruta, mtime, modelo e idioma. Un JSON que falta en disco no es acierto.
  - Modelos: `small`, `medium`, `large-v3-turbo` (★, repo `mobiuslabsgmbh/faster-whisper-large-v3-turbo`) y `large-v3`, con repo de Hugging Face, tamaño y VRAM aproximada.
  - Idiomas admitidos: `auto`, `es`, `en`, `pt`, `fr`, `de`, `it`. Otro código da `unknown_language` (texto nuevo en los tres catálogos).
  - Dispositivo: GPU con `int8_float16` si `system.tools.detect()` ve NVIDIA; si no, CPU con `int8`.
  - El audio se extrae con ffmpeg a 16 kHz mono antes de transcribir, también para los videos.
- **Descartadas**:
  - Migración 3 como la pide la spec: ya existe y cambiarla rompe bases de usuario.
  - Guardar el texto en la base: la decisión del usuario es solo metadatos.
  - Un modelo por defecto distinto de large-v3-turbo: la spec lo marca como ★.
- **Cómo revertir**: quitar la migración 4 y el paquete `transcription/`; la receta y la familia se quitan con el mismo commit.
- **Cómo comprobarla**: `pytest server/tests/unit/src/content_studio/transcription server/tests/unit/src/content_studio/db` y, con el venv instalado, `pytest -m local server/tests/unit/src/content_studio/transcription` (transcribe 3 s con `small`).
- **Pendiente**: `GET /engines` con los modelos y su estado (descargado o no) se hace en la spec de la API (T6) y del selector (T7).
