---
modulo: editor
actualizada: 2026-11-25
---

# Editor

## Qué resuelve

Permite organizar y editar audio, video e imágenes sin modificar los archivos de origen, grabar tomas y exportar el resultado.

## Qué hace hoy

- `uv run studio editor render --project <project.json>` encola `editor.render`; cada proyecto vive en `out/editor/<fecha>-<slug>/` con `project.json`, `media/` y `exports/`.
- La app permite editar audio, video e imágenes con alfa, transformar clips con keyframes y transiciones, y crear títulos rasterizados con presets. El visor WebGL2 y FFmpeg comparten el PNG del texto.
- El modelo v3 guarda velocidad de audio y video, corrección de color, LUT `.cube`, chroma key, modos de fusión y pistas de subtítulos vinculadas a proyectos de la 014.
- El Inspector ofrece velocidad, color, LUT, chroma y fusión; los subtítulos se previsualizan con JASSUB y se pueden quemar en video o exportar como SRT/VTT.
- Narración, Música, Limpiador, Subtítulos, Convertir, Mezcla y la cola permiten «Abrir en Editor». Las exportaciones del Editor se pueden mandar a Convertir, Normalizar, Subtítulos o Mezcla.
- Exporta WAV, MP3, FLAC, M4A y Opus; para video, MP4 H.264 o WebM VP9. La normalización y los tramos por marcadores son opcionales.
- El explorador local es de solo lectura. La grabación crea WAV mono de 24 bits y 48 kHz dentro del proyecto; los videos generan proxies en `.cache/proxies/`. Las fuentes originales no se modifican.
- Los proyectos v1 y v2 se migran a v3 al abrirse; los proyectos son JSON, no filas ni blobs de SQLite.
- Hablantes (spec 038): «Transcribir la mezcla» con «Identificar hablantes» (con el motor de hablantes instalado) y la pista de subtítulos dibuja un bloque por cue, con el color y el nombre de su hablante.

- Código: `server/src/content_studio/editor/` (proyecto, tiempos, efectos, proxies y render), `services/editor_render.py`, `api/routes/editor.py`, `api/routes/fs.py` y `cli/editor.py`.
- Cliente: `client/src/features/editor/` (timeline, inspector, títulos, subtítulos, visor y compositor) y `client/src/shared/navigation/` para «Abrir en Editor» y «Mandar a…».
- Pruebas: `server/tests/unit/src/content_studio/editor/`, `client/tests/unit/src/features/editor/` y `tests/e2e/editor/`.
- Decisiones (historial de git de `docs/process/WARNING/`): 017-proyecto-json, 017-latencia-grabacion, 017-preview-media-elements, 017-presupuesto-js, 018-proxies, 018-render-video, 018-transiciones, 018-paridad-preview-export, 019-texto-rasterizado, 019-control-velocidad, 019-lut-paridad, 019-chroma-paridad, 019-fusion-con-alfa y 019-pista-subtitulos.
- En 017–019, WebView2 no respondió a CDP y el runner e2e no terminaba; en la 020 ambos terminaron con exit 0 (`app-check` smoke con 26 capturas y `e2e`).

## Historial

- 2026-11-22: spec 017, editor de audio con timeline, preview, grabación, explorador y exportación.
- 2026-11-23: spec 018, edición visual con compositor WebGL2, keyframes, transiciones y exportación de video.
- 2026-11-23: spec 019, proyecto v3, texto rasterizado, velocidad, color, LUT, chroma, fusión, subtítulos e integración con secciones.
- 2026-11-25: spec 038 (hablantes): la pista de subtítulos dibuja sus cues por hablante y «Transcribir la mezcla» identifica hablantes.

- Los cuatro e2e nuevos de títulos, chroma/fusión, abrir desde Narración y ausencia de libass imprimieron PASS en corridas enfocadas.
- La caché global de Chromium no contenía la revisión requerida; las corridas usaron `PLAYWRIGHT_BROWSERS_PATH` de `017-editor-core`.
- Playwright siguió activo unos nueve minutos sin resumen agregado ni archivos de resultados; en la 020 el runner terminó solo con exit 0.

## Verificación 019 (2026-11-24)

- T8: render MP4 de 12 s con transcripción por la cola y dos subtítulos quemados; fuentes intactas por SHA-256.
- Cinco cuadros de vista previa y exportación: SSIM 0,9867–0,9915; sin halo verde y título sin solapar subtítulos.
- Sonoridad -21,5 LUFS y -5,2 dBTP; tono 439→440 Hz en los tramos a 2× y 0,5×.
- 190 pruebas unitarias del editor, 3 de integración con libass y 1 local pasan.
- Vitest: el `Picker` diferido de los selectores se precarga en `tests/unit/setup.ts`; el p99 bajó de 2,8 s a 0,65 s.
- «Mandar a Normalizar» se cubre con pruebas de cliente; app-check y e2e siguen en PENDING (CDP y runner).

## Verificación (2026-11-23)

- T8 usó medios sintéticos: video de 4 s, imagen con referencias geométricas y PNG RGBA con alfa transparente. El proyecto validó sin errores y las tres fuentes conservaron su SHA-256.
- MP4 H.264 NVENC: 1080×1920, 24 fps, 5,500 s. WebM VP9/Opus: 1080×1920, 24 fps, 5,508 s. Ambos midieron -21,6 LUFS; sincronía del destello y el transitorio: 15 ms.
- Siete pares de fotograma exacto del server y exportación MP4 dieron SSIM de 0,974366 a 0,997220. Image-reader confirmó logo visible sin halo, transición y zoom legibles.
- AC-6: proyecto de 40 clips y 60 s, 720p/30 fps; render 6,18 s, `.filter` de 26 395 bytes. La prueba local del editor pasó.
- E2E y app-check no entregaron un resultado final: el runner sigue en PENDING y WebView2 no respondió a CDP en tres corridas.

## Verificación (2026-11-22)

- El CLI encoló render WAV y MP3 con el worker desde un proyecto de prueba de 5 s. Ambos salieron a 48 kHz estéreo y 5,000 s; el WAV midió -21,8 LUFS/-21,1 dBTP y MP3 podcast -16,2 LUFS/-15,5 dBTP.
- El SHA-256 de la entrada coincide antes y después. Los espectrogramas `tmp/spec-017/export-1.png` y `export-2.png` muestran el tono continuo sin cortes.
- Los cuatro e2e del Editor pasan y Playwright listó 61 pruebas como aprobadas; el runner no terminó ni mostró exit 0, registrado entonces como pendiente; en la 020 el runner terminó con exit 0.
- 2026-11-24: verificación integral (023): el render guarda su resultado en el trabajo y la exportación entra en la biblioteca.
