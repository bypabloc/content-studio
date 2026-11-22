# 014: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo. Los medios de prueba se generan con ffmpeg dentro del test.

## 1. Ciclos TDD

#### Ciclo 1: documento y segmentación [AC-1, AC-5]

- **RED**: `subtitles/test_document.py` y `subtitles/test_segment.py`, con doctests.
- **GREEN**: `subtitles/{document,segment}.py`. `clean/exports.py` pasa a usar `segment` y sus golden files se regeneran en un commit aparte.
- **REFACTOR**: ninguno.

#### Ciclo 2: formatos y ASS [AC-2, AC-3]

- **RED**: `subtitles/test_formats.py` y `subtitles/test_ass.py` (golden files y validación con ffmpeg).
- **GREEN**: `subtitles/{formats,ass,styles}.py` y los presets incluidos.
- **REFACTOR**: ninguno.

#### Ciclo 3: orígenes y alineación [AC-4, AC-11 (server)]

- **RED**: `subtitles/test_sources.py` (los cuatro orígenes, con transcripción simulada) y `services/test_subtitles_create.py`.
- **GREEN**: `subtitles/sources.py`, `services/subtitles_create.py`, la migración 4 y `api/routes/subtitles.py` (CRUD).
- **REFACTOR**: ninguno.

#### Ciclo 4: fuentes [AC-8]

- **RED**: `subtitles/test_fonts.py`, con la lectura de la tabla `name` de una fuente incluida y la carpeta del sistema simulada.
- **GREEN**: `server/data/fonts/` (las fuentes OFL con sus licencias), `subtitles/fonts.py`, `GET /subtitles/fonts` y `/files` para las carpetas de fuentes.
- **REFACTOR**: ninguno.

#### Ciclo 5: quemar [AC-6, AC-7]

- **RED**: `subtitles/test_burn.py` (doctest de escape, ffmpeg real con libass y error sin libass).
- **GREEN**: `common/encode.py` (extraído de `clean/render.py`), `subtitles/burn.py`, `services/subtitles_burn.py` y `libass` en `system.detect()`.
- **REFACTOR**: `clean/render.py` usa `common/encode.py` y sus tests siguen verdes.

#### Ciclo 6: traducir [AC-12]

- **RED**: `services/test_subtitles_translate.py` (simulado) y un test `-m local` con `small`.
- **GREEN**: `task` en `transcription/transcribe_main.py` y `services/subtitles_translate.py`.
- **REFACTOR**: ninguno.

#### Ciclo 7: client [AC-9, AC-10]

- **RED**: `features/subtitles/ass.test.ts` (contra los golden files del server), `CueList.test.tsx` (editar, dividir, unir y palabras clave), `StylePanel.test.tsx`, `SubtitlesEditor.test.tsx` (autoguardado con debounce y atajos) y `SafeZones.test.tsx`.
- **GREEN**: `features/subtitles/*`, `jassub` (con import diferido para el budget), `safe-zones.json`, los botones «Subtitular» en el Limpiador y en Narración, y las líneas en `nav.ts` y `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 8: e2e y docs [AC-11]

- **RED**: los e2e `subtitles/happy-from-file`, `happy-from-cleaner`, `happy-from-narration`, `happy-import-edit-export`, `happy-burn-reels`, `neg-burn-no-libass` y `neg-import-invalid`.
- **GREEN**: las respuestas grabadas en `_api/subtitles/` y D-10.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/subtitles/{document,segment,formats,ass,styles,sources,fonts,burn}.py` | `unit` |
| Crear | `services/{subtitles_create,subtitles_burn,subtitles_translate}.py`, `api/routes/subtitles.py`, `common/encode.py` | `unit` |
| Modificar | `clean/{exports,render}.py`, `transcription/transcribe_main.py`, `system/tools.py`, `db/schema.py` (migración 4), `services/registry.py`, `api/routes/files.py`, `cli/main.py`, `messages/{es,en,pt}.json` | `unit` |
| Crear | `server/data/fonts/**` (OFL) | `validators` (excluir binarios), `spelling` (ignorar) |
| Crear | `client/src/features/subtitles/*` | `client-unit` |
| Modificar | `features/{cleaner,narration}/*Result*.tsx`, `app/nav.ts`, `messages/{es,en,pt}.json`, `client/package.json`, `bun.lock` | `client-unit`, `budget` |
| Crear | `tests/e2e/subtitles/*.e2e.ts`, `_api/subtitles/*` | `e2e` |
| Modificar | `AGENTS.md`, `docs/process/01-done/` (+ `subtitles.md`), README de datos (fuentes) | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Documento y segmentación | AC-1, AC-5 | — | `unit` | [x] |
| T2 | Formatos y ASS | AC-2, AC-3 | T1 | `unit` | [x] |
| T3 | Orígenes y alineación | AC-4 | T1 | `unit` | [x] |
| T4 | Fuentes | AC-8 | — | `unit` | [x] |
| T5 | Quemar | AC-6, AC-7 | T2, T4 | `unit` | [x] |
| T6 | Traducir | AC-12 | T3 | `unit`, `-m local` | [x] |
| T7 | Client | AC-9, AC-10 | T2–T6 | `client-unit`, `budget` | [x] |
| T8 | e2e y docs | AC-11 | T7 | `e2e` | [x] |
| T9 | Corridas reales | AC-6, AC-8, AC-11, AC-12 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: documento de subtítulos y segmentación configurable` (T1).
2. `test: regenerar golden files del SRT del limpiador con la segmentación nueva` (T1, commit aparte).
3. `feat: SRT, VTT y ASS con estilos clásico, redes y karaoke` (T2).
4. `feat: subtítulos desde archivo, limpiador, narración alineada o SRT importado` (T3).
5. `feat: fuentes OFL incluidas y fuentes del sistema` (T4).
6. `feat: quemar subtítulos con libass y el codificador compartido` (T5).
7. `feat: traducir la pista de subtítulos al inglés` (T6).
8. `feat: editor de subtítulos con vista previa exacta, zonas seguras y estilos` (T7).
9. `test: e2e de Subtítulos; docs` (T8 y las fichas).
