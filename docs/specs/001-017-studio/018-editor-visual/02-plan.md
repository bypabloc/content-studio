# 018: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: esquema v2 y keyframes [AC-1]

- **RED**: `editor/test_project.py` (migración v1 → v2, validación de transform, transiciones y enlaces), `editor/test_keyframes.py` y `model/keyframes.test.ts` con `fixtures/editor/keyframes-*.json`.
- **GREEN**: `editor/project.py` (v2 y `migrate`), `editor/keyframes.py`, `model/{types,validate,keyframes}.ts` y las operaciones de enlace en `ops.py`/`ops.ts`.
- **REFACTOR**: ninguno.

#### Ciclo 2: proxies y fotograma exacto [AC-4]

- **RED**: `editor/test_proxy.py` (tamaño, GOP, alfa conservado en VP9, hash de caché) y `api/routes/test_editor_frame.py`.
- **GREEN**: `editor/proxy.py`, `services/editor_proxy.py` y `GET /editor/projects/frame`.
- **REFACTOR**: ninguno.

#### Ciclo 3: render de capas y keyframes [AC-2]

- **RED**: `editor/test_render_video.py` (golden de expresiones por tramos y render real con colores y un PNG con alfa generados en `tmp/spec-018/`).
- **GREEN**: `editor/render_video.py` (base, capas, transform, opacidad, crop, rotación y expresiones) y `editor.render` con formatos de video.
- **REFACTOR**: si `render_video.py` pasa de 300 líneas, las expresiones van a `editor/expr.py`.

#### Ciclo 4: transiciones y escala [AC-3, AC-6]

- **RED**: los casos de cada transición en `test_render_video.py` y el proyecto de 40 clips con `-m local`.
- **GREEN**: `xfade` por pista y, si AC-6 lo exige, el render por tramos con `concat`.
- **REFACTOR**: ninguno.

#### Ciclo 5: compositor [AC-5]

- **RED**: `preview/compositor.test.ts` (matrices y orden de capas con un contexto WebGL simulado). El e2e `editor/parity-preview-export.e2e.ts` contra `fixtures/editor/parity-*.json` se integra en T6, cuando exista el visor, y se ejecuta antes de cerrar T7.
- **GREEN**: `preview/{compositor,shaders,transitions,useLayerSources}.ts`.
- **REFACTOR**: ninguno.

#### Ciclo 6: visor, inspector y línea de tiempo visual [AC-7]

- **RED**: `preview/Viewer.test.tsx`, `Inspector.test.tsx`, `KeyframeLane.test.tsx` y `TransitionZone.test.tsx`.
- **GREEN**: `preview/Viewer.tsx`, `Inspector.tsx`, `KeyframeLane.tsx`, `TransitionsPanel.tsx`, miniaturas en `ClipView.tsx` y el diálogo de exportación con video.
- **REFACTOR**: ninguno.

#### Ciclo 7: e2e y docs

- **RED**: los e2e `editor/happy-logo-keyframes-export`, `editor/happy-transition-fade` y `editor/neg-proxy-missing-source`.
- **GREEN**: respuestas grabadas en `_api/editor/`, `docs/process/01-done/editor.md` (sección visual) y `AGENTS.md`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/editor/{keyframes,proxy,render_video}.py`, `services/editor_proxy.py` | `unit` |
| Modificar | `editor/{project,ops}.py`, `services/editor_render.py`, `services/registry.py`, `api/routes/editor.py`, `messages/{es,en,pt}.json` | `unit` |
| Crear | `server/tests/fixtures/editor/{keyframes,parity,ops-link}-*.json` | `unit`, `client-unit`, `e2e` |
| Crear | `client/src/features/editor/preview/**`, `Inspector.tsx`, `KeyframeLane.tsx`, `TransitionsPanel.tsx` | `client-unit` |
| Modificar | `client/src/features/editor/{model/*,ClipView,Timeline,ExportDialog}.tsx`, `atoms/UIIcon`, `messages/{es,en,pt}.json` | `client-unit` |
| Crear | `tests/e2e/editor/{parity-preview-export,happy-logo-keyframes-export,happy-transition-fade,neg-proxy-missing-source}.e2e.ts` | `e2e` |
| Modificar | `docs/process/01-done/editor.md`, `AGENTS.md` | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Esquema v2 y keyframes | AC-1 | — | `unit`, `client-unit` | [x] |
| T2 | Proxies y fotograma exacto | AC-4 | T1 | `unit` | [x] |
| T3 | Render de capas y keyframes | AC-2 | T1 | `unit` | [x] |
| T4 | Transiciones y escala | AC-3, AC-6 | T3 | `unit`, `-m local` | [x] |
| T5 | Compositor | AC-5 | T1, T2 | `client-unit`, `e2e` | [x] |
| T6 | Visor, inspector y línea de tiempo | AC-7 | T5 | `client-unit` | [x] |
| T7 | e2e y docs | — | T4, T6 | `e2e` | [x] |
| T8 | Corrida real | AC-6 | T7 | verificación final | [x] |

## 4. Commits

1. `feat: proyecto v2 del editor con lienzo, pistas visuales y keyframes compartidos` (T1).
2. `feat: proxies de video y fotograma exacto del editor` (T2).
3. `feat: exportar capas con transformación y keyframes` (T3).
4. `feat: transiciones entre clips y render de proyectos grandes` (T4).
5. `feat: compositor WebGL2 de vista previa con paridad frente a la exportación` (T5).
6. `feat: visor, inspector, keyframes y transiciones en el editor` (T6).
7. `test: e2e del editor visual; docs` (T7).
