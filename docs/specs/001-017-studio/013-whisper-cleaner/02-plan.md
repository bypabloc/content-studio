# 013: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo. Los medios de prueba se generan con ffmpeg dentro del test (tonos, `anullsrc` y `testsrc` con contador), sin binarios versionados.

## 1. Ciclos TDD

#### Ciclo 1: plan y remap [AC-1, AC-2]

- **RED**: los doctests de `clean/plan.py` y `clean/test_plan.py` (casos de borde: sin palabras, una sola palabra, huecos iguales a `min_gap`, padding mayor que la mitad del hueco y cortes de menos de 50 ms).
- **GREEN**: `plan`, `keep_segments` y `remap`.
- **REFACTOR**: ninguno.

#### Ciclo 2: exportaciones [AC-5]

- **RED**: `clean/test_exports.py`, con golden files en `server/tests/unit/src/content_studio/clean/fixtures/`.
- **GREEN**: `clean/exports.py` (txt, json, srt, edl, xml y report).
- **REFACTOR**: el armado de SRT queda en una función que la 014 reusa (`subtitles/srt.py` si conviene ya).

#### Ciclo 3: render de audio [AC-3]

- **RED**: `clean/test_render.py::test_ac3_audio` (ffmpeg real, con el WAV generado en el test).
- **GREEN**: `clean/render.py` (el `filter_complex` en un archivo y `acrossfade`) y `common/ffmpeg.py` (`silencedetect` para la medición).
- **REFACTOR**: ninguno.

#### Ciclo 4: render de video [AC-4]

- **RED**: `clean/test_render_video.py` (MP4 de 10 s a 30 fps con `testsrc2` y el cuadro codificado en un píxel). Se prueba con `libx264` en CI, y NVENC con `-m local`.
- **GREEN**: el camino de video en `render.py` y la elección del codificador según `system.detect()`.
- **REFACTOR**: ninguno.

#### Ciclo 5: transcripción, caché y receta [AC-6, AC-9 (server)]

- **RED**: `transcription/test_cache.py`, `transcription/test_models.py` (catálogo y recomendado), `engines/test_recipes.py` (la receta nueva valida) y un test `-m local` que transcribe 3 s con `small`.
- **GREEN**: `transcription/{models,cache,transcribe_main}.py`, la migración 3, `services/transcribe.py`, la receta `faster-whisper.json` y `models` en `GET /engines`.
- **REFACTOR**: ninguno.

#### Ciclo 6: trabajos y API del limpiador [AC-7]

- **RED**: `services/test_clean_analyze.py`, `services/test_clean_render.py` (transcriptor simulado) y `api/routes/test_clean.py` (`/plan` y `/cuts`, con los editados a mano conservados).
- **GREEN**: `services/{clean_analyze,clean_render}.py`, `api/routes/clean.py`, `media/formats.py`, `studio clean <archivos> [--auto]` y los mensajes `clean.*`.
- **REFACTOR**: ninguno.

#### Ciclo 7: client [AC-7, AC-8, AC-9]

- **RED**: `shared/components/WhisperModelSelect.test.tsx`, `features/cleaner/CleanerPage.test.tsx` (lote y auto), `CleanReview.test.tsx` (regiones, replan, conservar las editadas, «escuchar sin cortes» y atajos) y `useSyncedMedia.test.ts` (sincronía entre video y onda).
- **GREEN**: `features/cleaner/*`, `shared/components/molecules/UIWhisperModelSelect/`, `shared/media/useSyncedMedia.ts`, los plugins Regions y Timeline en `Waveform` y las líneas en `nav.ts` y `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 8: migrar la evaluación, e2e y docs [AC-8, AC-10]

- **RED**: `test_structure.py::test_ac10_no_whisper_cli` y los e2e `cleaner/happy-review-render`, `cleaner/happy-batch-auto`, `cleaner/happy-audio-only` y `cleaner/neg-unsupported-file`.
- **GREEN**: D-7, las respuestas grabadas en `_api/clean/`, D-8 y el cierre de PENDING 010.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/clean/{plan,render,exports}.py` | `unit` |
| Crear | `server/src/content_studio/transcription/{models,cache,transcribe_main}.py`, `engines/recipes/faster-whisper.json` | `unit`, `-m local` |
| Crear | `services/{transcribe,clean_analyze,clean_render}.py`, `api/routes/clean.py`, `media/formats.py` | `unit` |
| Modificar | `db/schema.py` (migración 3), `common/ffmpeg.py`, `services/registry.py`, `api/routes/engines.py`, `cli/main.py`, `messages/{es,en,pt}.json` | `unit` |
| Modificar | `narration/evaluation/*`, `services/voice_check.py`, `voices/build.py`, `engines/recipes/cosyvoice.json` | `unit`, `-m local` |
| Crear | `client/src/features/cleaner/*`, `shared/components/molecules/UIWhisperModelSelect/`, `shared/media/useSyncedMedia.ts` | `client-unit` |
| Modificar | `shared/media/Waveform.tsx` (plugins), `app/nav.ts`, `messages/{es,en,pt}.json`, `features/welcome/*` (paquete recomendado) | `client-unit` |
| Crear | `tests/e2e/cleaner/*.e2e.ts`, `_api/clean/*` | `e2e` |
| Modificar | `narration/README.md`, `AGENTS.md`, `docs/process/01-done/` (+ `cleaner.md`) | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Plan y remap | AC-1, AC-2 | — | `unit` | [x] |
| T2 | Exportaciones | AC-5 | T1 | `unit` | [x] |
| T3 | Render de audio | AC-3 | T1 | `unit` | [ ] |
| T4 | Render de video | AC-4 | T3 | `unit`, `-m local` | [ ] |
| T5 | Transcripción y caché | AC-6 | — | `unit`, `-m local` | [ ] |
| T6 | Trabajos y API | AC-7 | T2–T5 | `unit` | [ ] |
| T7 | Client | AC-7, AC-8, AC-9 | T6 | `client-unit` | [ ] |
| T8 | Migrar la evaluación, e2e y docs | AC-8, AC-10 | T7 | `all`, `e2e` | [ ] |
| T9 | Corridas reales | AC-11 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: plan de cortes por huecos entre palabras y reasignación de tiempos` (T1).
2. `feat: exportar transcripción, SRT, EDL, XML e informe del limpiador` (T2).
3. `feat: render de audio limpio con crossfade en cada corte` (T3).
4. `feat: render de video limpio con corte exacto en el cuadro, NVENC o x264` (T4).
5. `feat: transcripción con faster-whisper, modelos elegibles y caché en disco` (T5).
6. `feat: trabajos de análisis y render del limpiador con API de revisión` (T6).
7. `feat: sección Limpiador con lote y revisión en la línea de tiempo` (T7).
8. `refactor: evaluación y chequeo de tomas con faster-whisper; e2e del limpiador` (T8 y las fichas).
