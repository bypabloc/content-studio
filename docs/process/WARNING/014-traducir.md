# 014: traducir al inglés (ciclo 6)

**Qué se decidió.**

- **Mismo servicio de whisper.** `subtitles.translate` corre `transcribe_main --task translate`, con su venv y su modelo (el recomendado por defecto). No hay módulo nuevo.
- **Sin tiempos por palabra.** Whisper en modo traducción no los da: cada segmento es un cue en inglés con sus tiempos (`subtitles/translate.py`). El editor lo advierte (ciclo 7).
- **Sin caché.** La caché de la 013 (`transcripts`) se indexa por modelo e idioma, no por tarea. Traducir no la usa, para no tocar esa tabla en este grupo.
- **Cierre en el worker.** Al terminar, `_chain` llama a `translate.finish`: guarda `tracks.en` en el documento del proyecto y exporta `<nombre>.en.srt` y `<nombre>.en.vtt` en la carpeta del trabajo.
- **Nombre de la exportación**: el stem del video del proyecto, como en el resto del proyecto.

**Dónde.** `transcription/transcribe_main.py` (`--task`), `subtitles/translate.py`, `services/subtitles_translate.py`, `jobs/worker.py` (rama de `_chain`), `services/registry.py`.

**Pendiente.** La prueba `-m local` con `small` de la spec (AC-12, con audio en español real) no está escrita ni corrida: ver `docs/process/PENDING/014-traduccion-real.md`.
