---
modulo: editor
actualizada: 2026-11-23
---

# Editor

## Qué resuelve

Permite organizar y editar audio, video e imágenes sin modificar los archivos de origen, grabar tomas y exportar el resultado.

## Qué hace hoy

- `uv run studio editor render --project <project.json>` encola `editor.render`; cada proyecto vive en `out/editor/<fecha>-<slug>/` con `project.json`, `media/` y `exports/`.
- La app permite editar pistas de audio y video, imágenes con alfa, transformaciones con keyframes y transiciones. El visor usa WebGL2 y la exportación compone video y audio desde el proyecto.
- Exporta WAV, MP3, FLAC, M4A y Opus; para video, MP4 H.264 o WebM VP9. La normalización y los tramos por marcadores son opcionales.
- El explorador local es de solo lectura. La grabación crea WAV mono de 24 bits y 48 kHz dentro del proyecto; los videos generan proxies en `.cache/proxies/`. Las fuentes originales no se modifican.
- Los proyectos v1 se migran a v2 al abrirse; los proyectos son JSON, no filas ni blobs de SQLite.

## Dónde vive

- Código: `server/src/content_studio/editor/` (proyecto, keyframes, proxies y render de video), `services/editor_render.py`, `api/routes/editor.py`, `api/routes/fs.py` y `cli/editor.py`.
- Cliente: `client/src/features/editor/` (timeline, inspector, visor y compositor) y átomos en `client/src/shared/components/atoms/`.
- Pruebas: `server/tests/unit/src/content_studio/editor/`, `client/tests/unit/src/features/editor/` y `tests/e2e/editor/`.
- Decisiones: [017-proyecto-json](../WARNING/017-proyecto-json.md), [017-latencia-grabacion](../WARNING/017-latencia-grabacion.md), [017-preview-media-elements](../WARNING/017-preview-media-elements.md), [017-presupuesto-js](../WARNING/017-presupuesto-js.md), [018-proxies](../WARNING/018-proxies.md), [018-render-video](../WARNING/018-render-video.md), [018-transiciones](../WARNING/018-transiciones.md) y [018-paridad-preview-export](../WARNING/018-paridad-preview-export.md).
- Pendiente: [017-app-check-y-flujo-real](../PENDING/017-app-check-y-flujo-real.md) (CDP de WebView2 y toma física).
- Pendiente 018: [018-e2e-runner](../PENDING/018-e2e-runner.md) (el runner no entrega su resultado final) y [018-app-check-cdp](../PENDING/018-app-check-cdp.md) (WebView2 no respondió a CDP en tres corridas).

## Historial

- 2026-11-22: spec 017, editor de audio con timeline, preview, grabación, explorador y exportación.
- 2026-11-23: spec 018, edición visual con compositor WebGL2, keyframes, transiciones y exportación de video.

## Verificación (2026-11-23)

- T8 usó medios sintéticos: video de 4 s, imagen con referencias geométricas y PNG RGBA con alfa transparente. El proyecto validó sin errores y las tres fuentes conservaron su SHA-256.
- MP4 H.264 NVENC: 1080×1920, 24 fps, 5,500 s. WebM VP9/Opus: 1080×1920, 24 fps, 5,508 s. Ambos midieron -21,6 LUFS; sincronía del destello y el transitorio: 15 ms.
- Siete pares de fotograma exacto del server y exportación MP4 dieron SSIM de 0,974366 a 0,997220. Image-reader confirmó logo visible sin halo, transición y zoom legibles.
- AC-6: proyecto de 40 clips y 60 s, 720p/30 fps; render 6,18 s, `.filter` de 26 395 bytes. La prueba local del editor pasó.
- E2E y app-check no entregaron un resultado final: el runner sigue en PENDING y WebView2 no respondió a CDP en tres corridas.

## Verificación (2026-11-22)

- El CLI encoló render WAV y MP3 con el worker desde un proyecto de prueba de 5 s. Ambos salieron a 48 kHz estéreo y 5,000 s; el WAV midió -21,8 LUFS/-21,1 dBTP y MP3 podcast -16,2 LUFS/-15,5 dBTP.
- El SHA-256 de la entrada coincide antes y después. Los espectrogramas `tmp/spec-017/export-1.png` y `export-2.png` muestran el tono continuo sin cortes.
- Los cuatro e2e del Editor pasan y Playwright listó 61 pruebas como aprobadas; el runner no terminó ni mostró exit 0, registrado en [017-e2e-runner](../PENDING/017-e2e-runner.md).
