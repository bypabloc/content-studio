# 014: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo.

## 1. Ciclos TDD

#### Ciclo 1: índice desde trabajos [AC-1]

- **RED**: `library/test_index.py` (registro al terminar un trabajo y backfill de la migración) y `db/test_schema.py` (migración 6, sin BLOB).
- **GREEN**: la migración 6, `library/index.py` y el registro en `jobs/worker.py` cuando un trabajo termina `done`.
- **REFACTOR**: ninguno.

#### Ciclo 2: carpetas vigiladas y miniaturas [AC-2]

- **RED**: `library/test_scan.py` y `library/test_thumbs.py` (caché de disco por `sha1(path+mtime)`).
- **GREEN**: `library/{scan,thumbs}.py`, `services/library_scan.py` y `GET /library/thumb/{id}`.
- **REFACTOR**: ninguno.

#### Ciclo 3: búsqueda y filtros [AC-3, AC-9 (server)]

- **RED**: `library/test_query.py` (cada filtro y orden, paginado) y `library/test_text_search.py`.
- **GREEN**: `library/{query,text_search}.py`, `GET /library` e índices SQL.
- **REFACTOR**: ninguno.

#### Ciclo 4: etiquetas y proyectos [AC-8]

- **RED**: `library/test_tags_projects.py`.
- **GREEN**: `library/tags.py`, `library/projects.py` y sus rutas.
- **REFACTOR**: ninguno.

#### Ciclo 5: acciones [AC-4, AC-5]

- **RED**: `library/test_actions.py` (origen, repetir, renombrar, mover, borrar y protegidos).
- **GREEN**: `library/actions.py` (`send2trash` en `server/pyproject.toml`), las rutas de acciones y `studio library list|scan|tag|trash`.
- **REFACTOR**: ninguno.

#### Ciclo 6: espacio [AC-6]

- **RED**: `library/test_storage.py`.
- **GREEN**: `library/storage.py` y `GET /library/storage`.
- **REFACTOR**: ninguno.

#### Ciclo 7: client [AC-7, AC-8, AC-9]

- **RED**: `features/library/{LibraryPage,LibraryGrid,LibraryList,ItemDetail,StorageView,FolderSidebar}.test.tsx` y `from_job` en Narración, Música, Limpiador, Subtítulos, Convertir y Mezcla (un test por sección, con el mismo hook `useFromJob`).
- **GREEN**: `features/library/*`, `shared/hooks/useFromJob.ts`, `?path=` en las secciones que no lo tenían, `@tanstack/react-virtual` y las líneas en `nav.ts` y `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 8: e2e y docs [AC-7, AC-8]

- **RED**: los e2e `library/happy-browse-play`, `library/happy-edit-repeat`, `library/happy-tags-projects`, `library/happy-send-to-cleaner`, `library/happy-trash-unchosen-takes`, `library/neg-rename-exists` y `library/neg-delete-reference`.
- **GREEN**: las respuestas grabadas en `_api/library/` y D-7.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/library/{index,scan,thumbs,query,text_search,tags,projects,actions,storage}.py` | `unit` |
| Crear | `services/library_scan.py`, `api/routes/library.py` | `unit` |
| Modificar | `db/schema.py` (migración 6), `jobs/worker.py`, `services/registry.py`, `cli/main.py`, `messages/es.json`, `server/pyproject.toml`, `uv.lock` | `unit` |
| Crear | `client/src/features/library/*`, `shared/hooks/useFromJob.ts` | `client-unit` |
| Modificar | las páginas de cada sección (`from_job` y `?path=`), `app/nav.ts`, `messages/es.json`, `client/package.json`, `bun.lock` | `client-unit`, `budget` |
| Crear | `tests/e2e/library/*.e2e.ts`, `_api/library/*` | `e2e` |
| Modificar | `AGENTS.md`, `docs/process/01-done/` (+ `library.md`) | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Índice desde trabajos | AC-1 | — | `unit` | [ ] |
| T2 | Carpetas y miniaturas | AC-2 | T1 | `unit` | [ ] |
| T3 | Búsqueda y filtros | AC-3, AC-9 | T1 | `unit` | [ ] |
| T4 | Etiquetas y proyectos | AC-8 | T1 | `unit` | [ ] |
| T5 | Acciones | AC-4, AC-5 | T1 | `unit`, `-m local` | [ ] |
| T6 | Espacio | AC-6 | T1 | `unit` | [ ] |
| T7 | Client | AC-7, AC-8, AC-9 | T2–T6 | `client-unit`, `budget` | [ ] |
| T8 | e2e y docs | AC-7, AC-8 | T7 | `e2e` | [ ] |
| T9 | Corrida real | — | T8 | verificación final | [ ] |

## 4. Commits

1. `feat: índice de la biblioteca con las salidas de los trabajos` (T1).
2. `feat: carpetas vigiladas y miniaturas en caché de disco` (T2).
3. `feat: búsqueda y filtros, también en el texto de guiones y transcripciones` (T3).
4. `feat: etiquetas y proyectos en la biblioteca` (T4).
5. `feat: repetir, mandar a, renombrar, mover y papelera desde la biblioteca` (T5).
6. `feat: resumen del espacio y tomas no elegidas` (T6).
7. `feat: sección Biblioteca en grilla y lista con detalle y reproductor` (T7).
8. `test: e2e de la Biblioteca; docs` (T8 y las fichas).
