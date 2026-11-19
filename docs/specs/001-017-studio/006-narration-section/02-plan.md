# 006: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo (server y client), con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: linter del guion [AC-1]

- **RED**: `narration/test_script_lint.py`, con un caso por regla (1, 2, 3, 6, 10, 11, 13 y 19) más uno limpio. También `estimate_seconds` en un doctest.
- **GREEN**: `narration/script_lint.py`, `POST /narration/lint` (`api/routes/narration.py`) y los textos `lint.*` en `messages/es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 2: media info y picos [AC-4]

- **RED**: `api/routes/test_media.py` (fixture `tests/.../fixtures/two_seconds.wav` generado con ffmpeg en el test) y `common/test_ffmpeg.py` (los comandos armados).
- **GREEN**: `common/ffmpeg.py` (`probe_duration`, `loudness`, `peaks`) y `api/routes/media.py`, con caché por `(path, mtime)`.
- **REFACTOR**: si `/files` y `/media` repiten la validación de rutas, se extrae `api/paths_guard.py`.

#### Ciclo 3: bloques en disco [AC-2]

- **RED**: `narration/test_pipeline.py::test_ac2_blocks_persisted`, con un motor falso (subclase de `TTSEngine` en el test que devuelve ruido determinista).
- **GREEN**: `pipeline.write_blocks(g, out_dir)` llamado desde `regenerate()` y `script.json`.
- **REFACTOR**: ninguno.

#### Ciclo 4: regenerar y tomas [AC-3, AC-5]

- **RED**: `services/test_narration_regenerate.py` (AC-3 con el motor falso) y `api/routes/test_jobs.py::test_ac5_star_unique`. La migración 2 entra en `test_schema.py`.
- **GREEN**: `--from-script` y `--only` en `tts.py`, `services/narration_regenerate.py` y su línea en `SERVICES`, `studio narration regenerate`, la migración 2, `group_key`, `GET /jobs?group_key=` y `POST /jobs/{id}/star`.
- **REFACTOR**: ninguno.

#### Ciclo 5: editor [AC-6, AC-9]

- **RED**: `features/narration/ScriptEditor.test.tsx` (subrayado y tooltip, contador y duración) y `useScriptImport.test.ts` (tipos válidos e inválidos).
- **GREEN**: `ScriptEditor.tsx`, `ScriptHighlight.tsx`, `useScriptLint.ts`, `useScriptImport.ts` y las claves `narration.*` en `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 6: opciones, licencia y generar [AC-7, AC-8]

- **RED**: `NarrationOptions.test.tsx` (las ★ y la memoria salen de `RecommendedSelect`, Avanzado y el diálogo de licencia) y `NarrationPage.test.tsx` (`Ctrl+Enter` hace `POST /jobs` con los `params`).
- **GREEN**: `NarrationPage.tsx`, `NarrationOptions.tsx`, `AdvancedOptions.tsx`, `LicenseDialog.tsx` (en `shared/components/`, porque la 008 y la 009 lo reusan) y la línea en `nav.ts`.
- **REFACTOR**: ninguno.

#### Ciclo 7: reproductor, resultado y evaluación [AC-8]

- **RED**: `shared/media/Player.test.tsx` (carga los picos, Espacio reproduce o pausa) y `NarrationResult.test.tsx` (la evaluación por párrafo con las diferencias resaltadas y Regenerar encola `narration.regenerate`).
- **GREEN**: `wavesurfer.js` en `client/package.json`, `shared/media/{Waveform,Player,useMediaInfo}.tsx` y `NarrationResult.tsx`. Si wavesurfer sube el bundle inicial por encima del budget, se carga con `import()` diferido (y se anota).
- **REFACTOR**: ninguno.

#### Ciclo 8: comparar tomas y e2e [AC-9, AC-10]

- **RED**: `CompareTakes.test.tsx` y los e2e `narration/happy-generate`, `happy-import-batch`, `neg-import-invalid`, `happy-compare-takes` y `neg-license-cancel`, con `_api` grabado.
- **GREEN**: `CompareTakes.tsx`, las respuestas grabadas, y la actualización de `narration/README.md`, `formato-guion.md` y `01-done/narration.md`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/narration/script_lint.py`, `api/routes/{narration,media}.py`, `services/narration_regenerate.py` | `test-runner --type=unit` |
| Modificar | `common/ffmpeg.py`, `narration/pipeline.py`, `narration/tts.py`, `narration/parser.py` (flags internos), `db/schema.py` (migración 2), `db/jobs.py`, `api/routes/jobs.py`, `cli/main.py`, `messages/es.json` | ídem |
| Crear | `client/src/features/narration/*`, `client/src/shared/media/*`, `client/src/shared/components/LicenseDialog.tsx` | `test-runner --type=client-unit` |
| Modificar | `client/src/app/nav.ts`, `client/messages/es.json`, `client/package.json`, `bun.lock`, `client/src/shared/api/schema.d.ts` (regenerado) | `client-typecheck`, `budget` |
| Crear | `tests/e2e/narration/*.e2e.ts`, `tests/e2e/_api/narration/*` | `test-runner --type=e2e` |
| Modificar | `server/data/narration/README.md`, `docs/formato-guion.md`, `docs/process/01-done/narration.md` | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Linter | AC-1 | — | `unit` | [x] |
| T2 | Media info y picos | AC-4 | — | `unit` | [x] |
| T3 | Bloques en disco | AC-2 | — | `unit` | [x] |
| T4 | Regenerar y tomas | AC-3, AC-5 | T3 | `unit` | [x] |
| T5 | Editor | AC-6, AC-9 | T1 | `client-unit` | [x] |
| T6 | Opciones y generar | AC-7, AC-8 | T5 | `client-unit` | [ ] |
| T7 | Reproductor y resultado | AC-8 | T2, T4, T6 | `client-unit`, `budget` | [ ] |
| T8 | Comparar y e2e | AC-9, AC-10 | T7 | `e2e` | [ ] |
| T9 | Corridas reales | AC-3, AC-8 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: linter del guion con las reglas de formato-guion en la API` (T1).
2. `feat: duración, LUFS y picos de un audio en la API` (T2).
3. `feat: la narración guarda sus bloques y script.json` (T3).
4. `feat: regenerar un párrafo como toma nueva y marcar la elegida` (T4).
5. `feat: editor de guion con avisos en vivo e importación` (T5).
6. `feat: sección Narración con opciones recomendadas y aviso de licencia` (T6).
7. `feat: reproductor con forma de onda y evaluación por párrafo` (T7).
8. `feat: comparar tomas; e2e de Narración` (T8 y docs).
