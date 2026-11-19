# 013: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: envolvente [AC-1, AC-2]

- **RED**: los doctests de `mix/envelope.py` y `mix/test_envelope.py`.
- **GREEN**: `speech_regions` y `gain_curve`.
- **REFACTOR**: ninguno.

#### Ciclo 2: render de audio [AC-3, AC-4]

- **RED**: `mix/test_mix_render.py` (medición por ventanas con `astats` y los casos de música corta y larga).
- **GREEN**: `mix/render.py` (`sendcmd`, `sidechaincompress`, `amix`, fades, `fit` y `normalize`) y `services/mix_render.py`.
- **REFACTOR**: el generador de `sendcmd` de la 012 (`media/reframe.py`) y este comparten `common/sendcmd.py`.

#### Ciclo 3: video [AC-5]

- **RED**: `mix/test_mix_video.py`.
- **GREEN**: `replace` y `under` en `render.py`.
- **REFACTOR**: ninguno.

#### Ciclo 4: API y proyectos

- **RED**: `api/routes/test_mix.py` (`prepare` con un acierto de caché, `PUT` de regiones, `curve` y la migración 5 sin BLOB).
- **GREEN**: `api/routes/mix.py`, `db/schema.py` (migración 5) y `studio mix --voice --music [--video] [--mode]`.
- **REFACTOR**: ninguno.

#### Ciclo 5: client [AC-6, AC-7]

- **RED**: `features/mix/MixPage.test.tsx` (ranuras y orígenes), `MixTimeline.test.tsx`, `useMixPreview.test.ts` y `shared/components/JobPicker.test.tsx`.
- **GREEN**: `features/mix/*`, `shared/components/JobPicker.tsx`, «Mandar a Mezclar» habilitado en Narración y Música, `?match=` en Música y las líneas en `nav.ts` y `es.json`.
- **REFACTOR**: si el `DurationField` de la 008 y `JobPicker` repiten el selector de trabajos, `DurationField` usa `JobPicker`.

#### Ciclo 6: e2e y docs [AC-7]

- **RED**: los e2e `mix/happy-send-and-generate`, `mix/happy-edit-ramps-render`, `mix/happy-video-under` y `mix/neg-music-too-short`.
- **GREEN**: las respuestas grabadas en `_api/mix/` y D-5.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/mix/{envelope,render}.py`, `services/mix_render.py`, `api/routes/mix.py`, `common/sendcmd.py` | `unit` |
| Modificar | `media/reframe.py`, `db/schema.py` (migración 5), `services/registry.py`, `cli/main.py`, `messages/es.json` | `unit` |
| Crear | `client/src/features/mix/*`, `shared/components/JobPicker.tsx` | `client-unit` |
| Modificar | `features/{narration,music}/*Result*.tsx`, `features/music/{MusicPage,DurationField}.tsx`, `app/nav.ts`, `messages/es.json` | `client-unit` |
| Crear | `tests/e2e/mix/*.e2e.ts`, `_api/mix/*` | `e2e` |
| Modificar | `server/data/music/README.md`, `docs/process/01-done/` (+ `mix.md`) | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Envolvente | AC-1, AC-2 | — | `unit` | [ ] |
| T2 | Render de audio | AC-3, AC-4 | T1 | `unit` | [ ] |
| T3 | Video | AC-5 | T2 | `unit` | [ ] |
| T4 | API y proyectos | — | T1 | `unit` | [ ] |
| T5 | Client | AC-6, AC-7 | T4 | `client-unit` | [ ] |
| T6 | e2e y docs | AC-7 | T5 | `e2e` | [ ] |
| T7 | Corrida real | AC-8 | T6 | verificación final | [ ] |

## 4. Commits

1. `feat: envolvente de ducking a partir de la transcripción` (T1).
2. `feat: render de mezcla con ducking por transcripción o sidechain y LUFS final` (T2).
3. `feat: mezcla sobre un video, reemplazando su audio o por debajo` (T3).
4. `feat: API de proyectos de mezcla con regiones editables` (T4).
5. `feat: sección Mezcla con rampas editables y vista previa WebAudio` (T5).
6. `test: e2e de Mezcla; docs` (T6 y las fichas).
