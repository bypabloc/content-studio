# 015: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: modelo y fixtures [AC-1]

- **RED**: `editor/test_project.py` y `editor/test_ops.py` leen `server/tests/fixtures/editor/{ops,invalid}-*.json`; doctests de `duration` y `validate`.
- **GREEN**: `editor/project.py` (esquema v1, `validate`, `duration`, `migrate` de identidad) y `editor/ops.py`.
- **REFACTOR**: ninguno.

#### Ciclo 2: espejo TypeScript [AC-1, AC-6, AC-7]

- **RED**: `model/ops.test.ts` (mismas fixtures, leídas con `import.meta.glob`), `model/history.test.ts` y `model/snap.test.ts`.
- **GREEN**: `features/editor/model/{types,ops,validate,history,snap}.ts`.
- **REFACTOR**: si `ops.ts` pasa de 300 líneas, se divide por grupo (clips, pistas, marcadores).

#### Ciclo 3: proyectos y explorador en la API [AC-2, AC-3, AC-10]

- **RED**: `api/routes/test_editor.py` (crear, abrir, `If-Match`, subir grabación, recientes, `missing_source`) y `api/routes/test_fs.py`.
- **GREEN**: `api/routes/{editor,fs}.py`, `editor/store.py` (leer y escribir con hash y escritura atómica `os.replace`) y las claves en `messages/es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 4: render de audio [AC-4, AC-5]

- **RED**: `editor/test_render_audio.py` (golden del grafo y render real con tonos generados en `tmp/spec-015/`).
- **GREEN**: `editor/render_audio.py`, `services/editor_render.py` (línea en `SERVICES`) y `studio editor render --project <ruta> --format wav [--normalize podcast]` en `cli/main.py`.
- **REFACTOR**: el armado de `-progress` se comparte con `media/convert.py` (013) si repite.

#### Ciclo 5: línea de tiempo y transporte [AC-7]

- **RED**: `Timeline.test.tsx` (mover, recortar, seleccionar varios, zoom, imán), `TrackHeader.test.tsx` y `Transport.test.tsx` (atajos).
- **GREEN**: `features/editor/{EditorPage,Timeline,TrackHeader,ClipView,Ruler,Transport}.tsx` y `useEditorDoc.ts` (estado, historial y guardado con debounce).
- **REFACTOR**: ninguno.

#### Ciclo 6: vista previa [AC-4]

- **RED**: `playback/scheduler.test.ts` (qué clips están activos, rampas de fade y corrección de deriva con un reloj simulado).
- **GREEN**: `playback/{scheduler,usePlayback}.ts`.
- **REFACTOR**: ninguno.

#### Ciclo 7: explorador, importar, soltar y grabar [AC-8, AC-9, AC-10]

- **RED**: `browser/FileBrowser.test.tsx`, `useTrackRecorder.test.ts` y `ClipMissing.test.tsx`.
- **GREEN**: `browser/{FileBrowser,FolderTree}.tsx`, `useNativeDrop.ts`, `useTrackRecorder.ts` (sobre la captura de la 008), `ExportDialog.tsx` y `@tauri-apps/plugin-dialog` en `package.json` con su permiso en `capabilities/`.
- **REFACTOR**: si la 008 y el editor repiten el selector de dispositivo, queda uno en `shared/media/InputDeviceSelect.tsx`.

#### Ciclo 8: e2e y docs [AC-8]

- **RED**: los e2e `editor/happy-browse-split-export`, `editor/happy-undo-redo`, `editor/happy-markers-export-parts` y `editor/neg-missing-source`.
- **GREEN**: las respuestas grabadas en `_api/editor/` y `_api/fs/`, `docs/process/01-done/editor.md` y la fila en `AGENTS.md`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/editor/{project,ops,store,render_audio}.py`, `services/editor_render.py`, `api/routes/{editor,fs}.py` | `unit` |
| Crear | `server/tests/fixtures/editor/*.json` | `unit`, `client-unit` |
| Modificar | `services/registry.py`, `api/app.py`, `cli/main.py`, `messages/es.json` | `unit` |
| Crear | `client/src/features/editor/**` (model, playback, browser, componentes) | `client-unit` |
| Modificar | `client/src/app/nav.ts`, `shared/icons.ts`, `client/messages/es.json`, `client/package.json`, `client/src-tauri/capabilities/*.json` | `client-unit`, `tauri-check` |
| Crear | `tests/e2e/editor/*.e2e.ts`, `_api/editor/*`, `_api/fs/*` | `e2e` |
| Modificar | `AGENTS.md`, `docs/process/01-done/` (+ `editor.md`), `docs/process/PENDING/005-desvios-d1-d8.md` | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Modelo y fixtures | AC-1 | — | `unit` | [ ] |
| T2 | Espejo TS, historial e imán | AC-1, AC-6, AC-7 | T1 | `client-unit` | [ ] |
| T3 | API de proyectos y explorador | AC-2, AC-3, AC-10 | T1 | `unit` | [ ] |
| T4 | Render de audio y CLI | AC-4, AC-5 | T1 | `unit` | [ ] |
| T5 | Línea de tiempo y transporte | AC-7 | T2, T3 | `client-unit` | [ ] |
| T6 | Vista previa | AC-4 | T5 | `client-unit` | [ ] |
| T7 | Explorador, importar, soltar y grabar | AC-8, AC-9, AC-10 | T5 | `client-unit` | [ ] |
| T8 | e2e y docs | AC-8 | T6, T7 | `e2e` | [ ] |
| T9 | Corrida real | AC-9 | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: modelo del proyecto del editor con fixtures compartidas` (T1).
2. `feat: espejo del modelo en el client con deshacer, rehacer e imán` (T2).
3. `feat: API de proyectos del editor y explorador de carpetas de solo lectura` (T3).
4. `feat: exportar el proyecto a audio con filter_complex y normalizar` (T4).
5. `feat: línea de tiempo multipista y transporte del editor` (T5).
6. `feat: vista previa de audio del editor con WebAudio` (T6).
7. `feat: explorador, importar, soltar desde Windows y grabar en pista` (T7).
8. `test: e2e del editor; docs` (T8).
