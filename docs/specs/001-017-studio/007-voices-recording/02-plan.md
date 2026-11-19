# 007: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Excepción pedida: `move-data` mueve las referencias actuales al perfil `default`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: perfiles y migración [AC-1, AC-2, AC-11]

- **RED**: `narration/test_profiles.py`, el paso 3 en `devtools/tests/unit/test_move_data.py` y `narration/test_parser.py::test_profile_flag`.
- **GREEN**: `narration/profiles.py`, el paso 3 en `MIGRATIONS`, `--profile` en el parser y en `pipeline`, y el catálogo con perfiles.
- **REFACTOR**: `reference_for()` es el único que arma rutas de referencia (se comprueba con `graphify query "reference"`).

#### Ciclo 2: kit y tomas [AC-5]

- **RED**: `narration/test_recording_kit.py` (estilos en orden, duración y ppm por estilo y guion por estilo) y `narration/test_takes.py`.
- **GREEN**: `narration/recording_kit.py` (con lo que sirve de `grabar/kit.py`), `narration/takes.py` y `api/routes/voices.py` (profiles, takes, choose y kit).
- **REFACTOR**: ninguno.

#### Ciclo 3: chequeo de una toma [AC-4]

- **RED**: `services/test_voice_check.py`, con WAVs sintéticos (pico alto, demasiado largo, pausa interna, ruido y uno correcto) y la transcripción simulada.
- **GREEN**: `services/voice_check.py`, su línea en `SERVICES`, las mediciones en `common/ffmpeg.py` (piso de ruido y pausas con `silencedetect`) y los códigos `voice.check.*` en `messages/es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 4: importar con consentimiento [AC-6]

- **RED**: `api/routes/test_voices_import.py` (422 sin `consent`, y el tramo de un video de fixture con la duración y el formato correctos).
- **GREEN**: `POST .../import`, la extracción con ffmpeg y el consentimiento en `profile.json`.
- **REFACTOR**: ninguno.

#### Ciclo 5: catálogo y construir [AC-7, AC-9 (server)]

- **RED**: `api/routes/test_voices_catalog.py` y `services/test_voice_build.py` (`build` simulado que emite el progreso por estilo).
- **GREEN**: `GET /voices/catalog`, `services/voice_build.py` y `@@progress` en `voices/build.py`.
- **REFACTOR**: ninguno.

#### Ciclo 6: captura en el client [AC-3]

- **RED**: `features/recording/capture/encodeWav.test.ts`, `levels.test.ts` (dBFS de pico y RMS) y `useRecorder.test.ts` (`getUserMedia` simulado: las restricciones sin procesado).
- **GREEN**: `recorder-worklet.ts`, `encodeWav.ts`, `levels.ts`, `useRecorder.ts` y `LevelMeter.tsx`. En `src-tauri`, el permiso del micrófono si hace falta.
- **REFACTOR**: ninguno.

#### Ciclo 7: pantallas [AC-8, AC-9]

- **RED**: `MyVoicesPage.test.tsx`, `ProfileDetail.test.tsx`, `RecordWizard.test.tsx`, `ImportReference.test.tsx`, `CatalogPage.test.tsx` y `VoiceSelect.test.tsx` (favoritas primero).
- **GREEN**: `features/voices/*`, `features/recording/*` y las líneas en `nav.ts` y `es.json`. El selector de voz de Narración usa `voices.favorites`.
- **REFACTOR**: ninguno.

#### Ciclo 8: borrar `grabar/`, e2e y docs [AC-8, AC-10]

- **RED**: `test_structure.py::test_ac10_no_legacy_recording` y los e2e `recording/happy-record-take`, `recording/neg-mic-denied`, `voices/happy-import-consent`, `voices/neg-import-no-consent` y `voices/happy-build-favorite`.
- **GREEN**: D-7 y D-8, más las respuestas grabadas en `_api/voices/`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/narration/{profiles,recording_kit,takes}.py`, `services/{voice_check,voice_build}.py`, `api/routes/voices.py` | `unit` |
| Modificar | `narration/parser.py`, `pipeline.py`, `voices/build.py`, `common/ffmpeg.py`, `services/registry.py`, `api/routes/catalog.py`, `messages/es.json` | `unit` |
| Modificar | `devtools/move_data.py` (paso 3) | `uv run pytest devtools -q` |
| Borrar | `server/src/content_studio/narration/grabar/**` y sus tests | `test_structure.py` |
| Modificar | `pyproject.toml` / `server/pyproject.toml` (sin `legacy`), `uv.lock`, `cspell.config.yaml` | `uv sync`, `spelling` |
| Crear | `client/src/features/voices/*`, `client/src/features/recording/**` | `client-unit` |
| Modificar | `client/src/app/nav.ts`, `client/messages/es.json`, `features/narration/NarrationOptions.tsx` (favoritas y perfiles), `src-tauri/src/lib.rs` (permiso del micrófono) | `client-unit`, `tauri-check` |
| Crear | `tests/e2e/{voices,recording}/*.e2e.ts`, `_api/voices/*` | `e2e` |
| Modificar | `server/data/narration/docs/scripts/README.md`, `narration/README.md`, `AGENTS.md`, `docs/process/01-done/` | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Perfiles y migración | AC-1, AC-2, AC-11 | — | `unit` | [ ] |
| T2 | Kit y tomas | AC-5 | T1 | `unit` | [ ] |
| T3 | Chequeo | AC-4 | T2 | `unit` | [ ] |
| T4 | Importar | AC-6 | T2 | `unit` | [ ] |
| T5 | Catálogo y construir | AC-7 | — | `unit` | [ ] |
| T6 | Captura | AC-3 | — | `client-unit` | [ ] |
| T7 | Pantallas | AC-8, AC-9 | T1–T6 | `client-unit` | [ ] |
| T8 | Borrar `grabar/`, e2e y docs | AC-8, AC-10 | T7 | `all`, `e2e` | [ ] |
| T9 | Migración y corridas reales | AC-1, AC-7, AC-11 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: perfiles de voz propios y migración del juego actual al perfil default` (T1).
2. `feat: kit de grabación y tomas por estilo en la API` (T2).
3. `feat: chequeo automático de una toma (bordes, pico, duración, ruido y texto)` (T3).
4. `feat: importar una referencia desde audio o video con permiso del dueño` (T4).
5. `feat: catálogo de voces libres y construir como trabajo de la cola` (T5).
6. `feat: captura PCM sin procesado y WAV de 24 bits en el client` (T6).
7. `feat: secciones Mis voces, Grabar y Catálogo` (T7).
8. `refactor: se borra el CLI interactivo de grabación y el grupo legacy` (T8, docs y fichas).
