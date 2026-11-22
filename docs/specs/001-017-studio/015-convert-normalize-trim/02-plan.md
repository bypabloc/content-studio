# 015: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo. Los medios se generan con ffmpeg dentro del test (`sine`, `anoisesrc`, `testsrc2` y `color`).

## 1. Ciclos TDD

#### Ciclo 1: catálogo y armador [AC-1]

- **RED**: `media/test_convert.py` (golden files de argumentos por formato y `codec_unavailable`).
- **GREEN**: `media/formats.py` (salidas), `media/convert.py` y los codecs disponibles en `system.detect()` (`ffmpeg -encoders`).
- **REFACTOR**: ninguno.

#### Ciclo 2: render de conversión y GIF [AC-2, AC-3]

- **RED**: `media/test_convert_render.py` (ffmpeg real).
- **GREEN**: `services/media_convert.py`, el progreso con `-progress pipe:1` y la paleta en dos pasadas para GIF.
- **REFACTOR**: el parseo de `-progress` va a `common/ffmpeg.py`, y `clean/render.py` y `subtitles/burn.py` lo reusan.

#### Ciclo 3: presets y encuadre fijo [AC-4]

- **RED**: `media/test_presets.py` (★ según el aspecto) y `media/test_reframe.py` (`center`, `manual`, `fit-bars` y `fit-blur`).
- **GREEN**: `media/presets.py`, `media/reframe.py` (los cuatro modos fijos) y `GET /media/frame`.
- **REFACTOR**: ninguno.

#### Ciclo 4: seguir a la persona [AC-5]

- **RED**: `vision/test_smooth.py` (suavizado puro), `engines/test_recipes.py` (`vision.json` valida) y un test `-m local` de detección con la imagen de prueba.
- **GREEN**: `vision/{smooth,face_track_main}.py`, la receta `vision.json`, `services/media_reframe_track.py` y el `sendcmd` en `reframe.py`.
- **REFACTOR**: ninguno.

#### Ciclo 5: normalizar [AC-6]

- **RED**: `media/test_normalize.py` (dos pasadas, medición con `ebur128`, video copiado y `reference_protected`).
- **GREEN**: `media/normalize.py` y `services/media_normalize.py`.
- **REFACTOR**: la masterización de la narración (`--master voice`), si repite la lógica de dos pasadas, pasa a usar `normalize.py` (con las fixtures de caracterización iguales; si cambian, en un commit aparte).

#### Ciclo 6: recortar, unir y dividir [AC-7, AC-8, AC-9]

- **RED**: `media/test_edit.py`.
- **GREEN**: `media/edit.py` y `services/{media_trim,media_concat,media_split}.py`. `remove` reusa `clean/render.py`.
- **REFACTOR**: ninguno.

#### Ciclo 7: pantallas [AC-10, AC-11]

- **RED**: `features/convert/ConvertPage.test.tsx`, `FormatPicker.test.tsx`, `ReframePreview.test.tsx`, `features/normalize/NormalizePage.test.tsx` (A/B y la tabla antes/después). Recortar, unir y dividir no tienen pantalla: su cobertura es la de `test_edit.py` y `api/routes/test_media.py`.
- **GREEN**: `features/{convert,normalize,edit}/*`, `shared/components/organisms/UIErrorDetailDialog/` y las líneas en `nav.ts` y `es.json`.
- **REFACTOR**: si la tabla de lote de Convertir y la de Normalizar son iguales, se extrae `shared/components/organisms/UIBatchTable/`.

#### Ciclo 8: e2e, CLI y docs

- **RED**: los e2e `convert/happy-batch-mp3`, `convert/happy-reels-manual`, `convert/neg-codec-unavailable`, `normalize/happy-podcast-ab` y `normalize/neg-reference-protected`. Los e2e de edición son del Editor (017).
- **GREEN**: `studio convert|normalize|trim|concat|split`, las respuestas grabadas en `_api/media/` y D-7.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/media/{convert,presets,reframe,normalize,edit}.py`, `vision/{smooth,face_track_main}.py`, `engines/recipes/vision.json` | `unit`, `-m local` |
| Crear | `services/{media_convert,media_reframe_track,media_normalize,media_trim,media_concat,media_split}.py` | `unit` |
| Modificar | `media/formats.py`, `common/ffmpeg.py`, `system/tools.py`, `api/routes/media.py` (`/frame`), `services/registry.py`, `cli/main.py`, `messages/{es,en,pt}.json`, `clean/render.py`, `subtitles/burn.py`, `narration/audio.py` (si aplica) | `unit` |
| Crear | `client/src/features/{convert,normalize,edit}/*`, `shared/components/{ErrorDetailDialog,BatchTable}.tsx` | `client-unit` |
| Modificar | `client/src/app/nav.ts`, `messages/{es,en,pt}.json` | `client-unit` |
| Crear | `tests/e2e/{convert,normalize,edit}/*.e2e.ts`, `_api/media/*` | `e2e` |
| Modificar | `AGENTS.md`, `docs/process/01-done/` (+ `convert.md`, `edit.md`) | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Catálogo y armador | AC-1 | — | `unit` | [x] |
| T2 | Render y GIF | AC-2, AC-3 | T1 | `unit` | [x] |
| T3 | Presets y encuadre fijo | AC-4 | T2 | `unit` | [ ] |
| T4 | Seguir a la persona | AC-5 | T3 | `unit`, `-m local` | [ ] |
| T5 | Normalizar | AC-6 | — | `unit` | [ ] |
| T6 | Recortar, unir y dividir | AC-7, AC-8, AC-9 | — | `unit` | [ ] |
| T7 | Pantallas | AC-10, AC-11 | T1–T6 | `client-unit` | [ ] |
| T8 | e2e, CLI y docs | — | T7 | `e2e` | [ ] |
| T9 | Corridas reales | AC-12 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: catálogo de formatos y armador de comandos de conversión` (T1).
2. `feat: convertir audio, video y GIF con progreso` (T2).
3. `feat: presets de redes con encuadre centrado, manual, barras o desenfoque` (T3).
4. `feat: reencuadre que sigue a la persona con YuNet` (T4).
5. `feat: normalizar a LUFS en dos pasadas con medición antes y después` (T5).
6. `feat: recortar, unir con crossfade y dividir en partes` (T6).
7. `feat: secciones Convertir y Normalizar` (T7).
8. `test: e2e de las herramientas de medios; CLI y docs` (T8 y las fichas).
