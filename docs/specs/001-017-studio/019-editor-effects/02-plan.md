# 019: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: esquema v3 y tiempos [AC-1]

- **RED**: `editor/test_project.py` (migración v2 → v3), `editor/test_timing.py` y `model/timing.test.ts` con `fixtures/editor/timing-*.json`.
- **GREEN**: `editor/{project,timing}.py` y `model/{types,validate,timing}.ts`; `ops` usa la duración con velocidad.
- **REFACTOR**: ninguno.

#### Ciclo 2: texto [AC-2]

- **RED**: `text/rasterize.test.ts` (tamaño, alfa y hash) y `TextInspector.test.tsx`.
- **GREEN**: `text/{rasterize,fonts,presets}.ts`, `TextInspector.tsx` y `GET /fonts/list` si la 014 no lo expone ya.
- **REFACTOR**: ninguno.

#### Ciclo 3: velocidad [AC-4]

- **RED**: `editor/test_render_audio.py`, `editor/test_render_video.py` y `editor/test_video_transitions.py` (speed y audio con FFT).
- **GREEN**: `setpts` y `atempo` en `render_video.py` y `render_audio.py`; `playbackRate` en `playback/` y `preview/`.
- **REFACTOR**: ninguno.

#### Ciclo 4: color, LUT, chroma y fusión [AC-3, AC-5]

- **RED**: `editor/test_effects.py` (golden de la cadena y render real de cuadros) y el e2e `editor/parity-effects.e2e.ts`.
- **GREEN**: `editor/effects.py`, su uso en `render_video.py`, `preview/effects.glsl.ts` y los inspectores `ColorInspector.tsx` y `EffectsInspector.tsx` (cuentagotas).
- **REFACTOR**: si `render_video.py` pasa de 300 líneas, la cadena por clip va a `editor/clip_chain.py`.

#### Ciclo 5: subtítulos [AC-6]

- **RED**: `editor/test_render_subtitles.py` y `SubtitleTrack.test.tsx`.
- **GREEN**: pista `subtitles` en `render_video.py` (reusando el armado del ASS de `subtitles/`), `SubtitleTrack.tsx` con JASSUB.
- **REFACTOR**: si `subtitles.burn` y el editor arman igual el filtro, queda una función en `subtitles/burn.py` que usan los dos.

#### Ciclo 6: «Abrir en Editor» y «Mandar a…» [AC-7]

- **RED**: `shared/navigation/sendTo.test.ts`, `useEditorAdd.test.ts` y los tests de resultados de cada sección (el botón existe y navega con `?add=`).
- **GREEN**: `sendTo.ts`, `?add=` en `EditorPage.tsx` y los botones en Narración, Música, Limpiador, Subtítulos, Convertir, Mezcla y `JobRow`.
- **REFACTOR**: «Mandar a Mezclar» de la 016 pasa a usar `sendTo.ts`.

#### Ciclo 7: e2e y docs

- **RED**: los e2e `editor/happy-title-lower-third`, `editor/happy-chroma-blend`, `editor/happy-open-from-narration` y `editor/neg-no-libass`.
- **GREEN**: respuestas grabadas, `docs/process/01-done/editor.md` (efectos) y `AGENTS.md`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/editor/{timing,effects}.py` | `unit` |
| Modificar | `editor/{project,ops,render_video,render_audio}.py`, `subtitles/*` (si se comparte el filtro), `api/routes/editor.py`, `messages/{es,en,pt}.json` | `unit` |
| Crear | `server/tests/fixtures/editor/{timing,parity-effects}-*.json` y LUT `.cube` de prueba | `unit`, `e2e` |
| Crear | `client/src/features/editor/text/**`, `preview/effects.glsl.ts`, `{Text,Color,Effects}Inspector.tsx`, `SubtitleTrack.tsx`, `shared/navigation/sendTo.ts` | `client-unit` |
| Modificar | `features/{narration,music,cleaner,subtitles,convert,mix}/*Result*.tsx`, `features/queue/JobRow.tsx`, `features/editor/{EditorPage,preview/*,playback/*}`, `messages/{es,en,pt}.json` | `client-unit` |
| Crear | `tests/e2e/editor/{parity-effects,happy-title-lower-third,happy-chroma-blend,happy-open-from-narration,neg-no-libass}.e2e.ts` | `e2e` |
| Modificar | `docs/process/01-done/editor.md`, `AGENTS.md` | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Esquema v3 y tiempos | AC-1 | — | `unit`, `client-unit` | [ ] |
| T2 | Texto | AC-2 | T1 | `client-unit` | [ ] |
| T3 | Velocidad | AC-4 | T1 | `unit` | [ ] |
| T4 | Color, LUT, chroma y fusión | AC-3, AC-5 | T1 | `unit`, `e2e` | [ ] |
| T5 | Subtítulos | AC-6 | T1 | `unit` | [ ] |
| T6 | Abrir en Editor y Mandar a | AC-7 | — | `client-unit` | [ ] |
| T7 | e2e y docs | — | T2–T6 | `e2e` | [ ] |
| T8 | Corrida real | — | T7 | verificación final | [ ] |

## 4. Commits

1. `feat: proyecto v3 del editor con velocidad y efectos en el modelo` (T1).
2. `feat: clips de texto rasterizados con presets de título` (T2).
3. `feat: velocidad de clips con tono conservado` (T3).
4. `feat: color, LUT, chroma key y modos de fusión con paridad de vista previa` (T4).
5. `feat: pista de subtítulos en el editor` (T5).
6. `feat: abrir en el editor desde las secciones y mandar la exportación` (T6).
7. `test: e2e de efectos del editor; docs` (T7).
