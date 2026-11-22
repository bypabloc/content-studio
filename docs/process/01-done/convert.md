---
modulo: convert
actualizada: 2026-11-22
---

# Convertir y normalizar

## Qué resuelve

Convierte audio y video a los formatos estándar, a presets de redes con encuadre, a GIF o a audio de un video. Normaliza la sonoridad a un preset en dos pasadas, y deja escuchar el original y el resultado (A/B).

## Qué hace hoy

- `uv run studio convert <archivos> --target <formato> [--option clave=valor]...`: un trabajo por archivo. Ejemplo: `studio convert charla.wav --target mp3 --option vbr=2`. Para Redes: `studio convert clip.mp4 --target mp4-h264 --option width=1080 --option height=1920 --reframe center` (`--reframe`: `center`, `fit-bars` o `fit-blur`; el manual y seguir a la persona van desde la app).
- `uv run studio normalize <archivos> [--preset youtube|podcast|broadcast|custom] [--target LUFS] [--enhance]`: mide con `ebur128`, aplica `loudnorm` lineal en dos pasadas y deja `normalized.<ext>` y `result.json` (medidas antes y después). El pico real queda en −1 dBTP o menos.
- Sección **Convertir**: formato ★, calidad, preset de red y encuadre (centrado, manual, barras, desenfoque o seguir a la persona), con la tabla de trabajos y el error con su detalle. **Normalizar**: preset ★ según haya video, medidas antes y después, «Mejorar voz» y el A/B.
- Salidas: `out/media/<fecha>-<id>-media-<tipo>/`, con `params.json`. La entrada no se modifica.
- Un códec que este ffmpeg no trae (`codec_unavailable`) y una referencia de voz (`reference_protected`) se rechazan al encolar, con su motivo.

## Dónde vive

- Código: `server/src/content_studio/media/` (`convert`, `presets`, `reframe`, `normalize`, `formats`), `services/media_{convert,normalize,reframe_track}.py`, `vision/` (seguir a la persona con YuNet) y `cli/media.py`.
- Cliente: `client/src/features/convert/` y `client/src/features/normalize/`.
- Pruebas: unitarias en `server/tests/unit/src/content_studio/media/` y `cli/test_media.py`; cliente en `client/tests/unit/src/features/{convert,normalize}/`; e2e en `tests/e2e/convert/` y `tests/e2e/normalize/` (sobre `_api/media/`).
- Decisiones: WARNING [015-armador-de-comandos](../WARNING/015-armador-de-comandos.md), [015-render-de-conversion](../WARNING/015-render-de-conversion.md), [015-presets-y-encuadre](../WARNING/015-presets-y-encuadre.md), [015-normalizar](../WARNING/015-normalizar.md), [015-seguir-a-la-persona](../WARNING/015-seguir-a-la-persona.md) y [015-pantallas-convertir-normalizar](../WARNING/015-pantallas-convertir-normalizar.md).

## Historial

- 2026-11-22: spec 015 (T1 a T8): catálogo y armador, render y GIF, presets y encuadre, seguir a la persona, normalizar, pantallas del cliente, CLI y e2e.

## Verificación

- Pendiente: corridas reales de cada formato, la escucha del A/B y la revisión de las pantallas (T9, con sus fichas en PENDING).
