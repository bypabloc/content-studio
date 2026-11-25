---
modulo: subtitulos
actualizada: 2026-11-25
---

# Subtítulos

## Qué resuelve

Crea subtítulos desde un archivo transcrito, el limpiador o una narración (con el texto del guion), o importa un SRT o VTT. Se editan, se les da estilo, se exportan o se queman en el video.

## Qué hace hoy

- Crear desde un archivo (transcripción con faster-whisper), desde el limpiador («Subtitular» con la última render del análisis, sin transcribir de nuevo), desde una narración (texto del guion, tiempos alineados) o importando SRT o VTT.
- Editor: texto, tiempos, dividir, unir y palabras clave; vista previa con JASSUB; zonas seguras de redes; presets y estilos propios; guardado automático.
- Exportar SRT, VTT o ASS a `out/subtitles/`.
- Hablantes (spec 038): cada cue muestra su hablante con su color y lo cambia en su selector; la leyenda renombra y cambia el color; la vista previa pinta por hablante; exportar SRT, VTT o ASS con los nombres («Incluir nombres de hablantes»). Crear con «Identificar hablantes» (modelo e idioma de Transcripción), con el motor de hablantes instalado.
- Quemar en el video con ffmpeg y libass (estilo redes con la palabra resaltada). Traducir la pista al inglés (`tracks.en`, `.en.srt` y `.en.vtt`).
- Fuentes incluidas (OFL) y las instaladas en el sistema.

## Dónde vive

- Server: `server/src/content_studio/subtitles/`, `services/subtitles_*.py`, `api/routes/subtitles.py` y la migración 5 (`subtitle_projects`).
- Client: `client/src/features/subtitles/`; los botones «Subtitular» están en `features/cleaner/CleanReview.tsx` y `features/narration/NarrationResult.tsx`.
- Pruebas: e2e en `tests/e2e/subtitles/` (11 specs sobre la API grabada en `tests/e2e/_api/subtitles/`).
- Decisiones: WARNING `014-*` y `038-*` en `docs/process/WARNING/`.

## Historial

- 2026-11-25: 038 (subtítulos con hablantes): el documento guarda hablantes y el server los segmenta, pinta y exporta (fase 1); el cliente muestra chip, leyenda, vista previa y exportación con nombres (fase 2).
- 2026-11-24: traducir a cualquier idioma, corregir con un glosario y sugerir palabras clave con el asistente local; la pista va a `tracks[<idioma>]` (spec 021).
- 2026-11-22: spec 014 cerrada (PR #87, merge `f86b829`).
