# 008: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: plan y ajuste de duración [AC-1, AC-2]

- **RED**: los doctests de `plan_duration` y `music/test_duration.py::test_ac2_fit_exact_with_fade` (tono sintético generado con ffmpeg en `tmp_path`).
- **GREEN**: `music/duration.py` (`plan_duration`, `fit` y el comando de fade) y `validate` con `duration_over_max`.
- **REFACTOR**: el recorte de silencio que ya existía pasa a `duration.py` si estaba suelto en `music_main.py`.

#### Ciclo 2: intentos si sale corta [AC-3]

- **RED**: `music/test_music_main.py::test_ac3_retries_when_short`, con un motor falso (subclase de `MusicEngine` en el test).
- **GREEN**: el bucle de intentos en `music_main.py`, `result.warning`, `@@progress` por intento y `music_short` en `messages/es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 3: categorías y catálogo [AC-4]

- **RED**: `music/test_styles.py` (todo preset tiene una `category` válida) y `api/routes/test_music.py` (`GET /music/styles`).
- **GREEN**: `category` y `mood` en `styles.py`, `styles_catalog()` y `api/routes/music.py`.
- **REFACTOR**: si `styles.py` pasa las 300 líneas, se divide por familia (`styles_base.py` y `styles_extra.py`), que es lo que el baseline permite si ya estaba ahí.

#### Ciclo 4: muestras [AC-5]

- **RED**: `services/test_music_samples.py` (saltea las existentes, `force` y el progreso por preset).
- **GREEN**: `services/music_samples.py` y su línea en `SERVICES`, `/files` para `samples/`, `.gitignore`, `worktree prepare` (enlace de `samples/`) y `studio music samples`.
- **REFACTOR**: ninguno.

#### Ciclo 5: duración en el client [AC-6]

- **RED**: `features/music/DurationField.test.tsx` (mm:ss, presets, máximo por motor, igualar a narración y a archivo).
- **GREEN**: `DurationField.tsx` y `parseClock.ts` (mm:ss ↔ segundos, con test).
- **REFACTOR**: ninguno.

#### Ciclo 6: estilos y texto libre [AC-7]

- **RED**: `StyleBrowser.test.tsx` (filtros, favoritos y selección múltiple), `FreeTextStyle.test.tsx` y `useTapTempo.test.ts`.
- **GREEN**: `StyleBrowser.tsx`, `StyleCard.tsx` (▶ de la muestra), `FreeTextStyle.tsx`, `useTapTempo.ts` y las claves `music.*` en `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 7: pantalla, variantes y comparar [AC-8]

- **RED**: `MusicPage.test.tsx` (`POST /jobs` con `params` correctos para 2 estilos y 2 variantes) y `shared/components/CompareTakes.test.tsx` (columnas configurables; los tests de la 006 siguen verdes).
- **GREEN**: `git mv` de `CompareTakes` a `shared/components/` y su generalización, `MusicPage.tsx`, `MusicOptions.tsx`, `group_key` en el servicio de música y la línea en `nav.ts`.
- **REFACTOR**: ninguno.

#### Ciclo 8: e2e y docs [AC-8]

- **RED**: los e2e `music/happy-generate-compare`, `music/happy-match-narration`, `music/neg-free-text-incomplete` y `music/neg-duration-over-max`.
- **GREEN**: las respuestas grabadas en `_api/music/` y D-7.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/music/duration.py`, `services/music_samples.py`, `api/routes/music.py` | `unit` |
| Modificar | `music/music_main.py`, `music/styles.py`, `music/parser.py` (validación), `services/music.py` (`group_key`), `services/registry.py`, `api/routes/files.py`, `cli/main.py`, `messages/es.json` | `unit` |
| Modificar | `.gitignore`, `devtools/worktree.py` (`samples/`) | `uv run pytest devtools -q` |
| Crear | `client/src/features/music/*` | `client-unit` |
| Mover | `client/src/features/narration/CompareTakes.tsx` → `client/src/shared/components/` | `client-unit` |
| Modificar | `client/src/app/nav.ts`, `client/messages/es.json`, `features/narration/*` (import de `CompareTakes`) | `client-typecheck` |
| Crear | `tests/e2e/music/*.e2e.ts`, `_api/music/*` | `e2e` |
| Modificar | `server/data/music/README.md`, `ESTILOS.md`, `docs/process/01-done/music.md` | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Plan y ajuste | AC-1, AC-2 | — | `unit` | [ ] |
| T2 | Intentos | AC-3 | T1 | `unit` | [ ] |
| T3 | Categorías y API | AC-4 | — | `unit` | [ ] |
| T4 | Muestras | AC-5 | T3 | `unit` | [ ] |
| T5 | Duración (client) | AC-6 | — | `client-unit` | [ ] |
| T6 | Estilos y texto libre | AC-7 | T3 | `client-unit` | [ ] |
| T7 | Pantalla y comparar | AC-8 | T5, T6 | `client-unit` | [ ] |
| T8 | e2e y docs | AC-8 | T7 | `e2e` | [ ] |
| T9 | Corridas reales | AC-9 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: duración exacta en música con margen, recorte y fade` (T1).
2. `feat: regenerar la pista si sale más corta que lo pedido` (T2).
3. `feat: categorías de los presets y catálogo de estilos en la API` (T3).
4. `feat: muestras de 10 s por preset como trabajo reanudable` (T4).
5. `feat: campo de duración con presets e igualar a una narración o un video` (T5).
6. `feat: buscador de estilos, favoritos y texto libre guiado` (T6).
7. `feat: sección Música con variantes para comparar y elegir` (T7).
8. `test: e2e de Música; docs de duración exacta` (T8 y las fichas).
