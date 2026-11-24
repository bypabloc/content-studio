# 021: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo, con cobertura ≥ 80 % por archivo. Ningún test de CI carga un modelo: el LLM se simula con un servidor HTTP falso (`http.server`) que devuelve respuestas fijas.

## 1. Ciclos TDD

#### Ciclo 1: receta y modelos [AC-1]

- **RED**: `engines/test_recipes.py` (`llama-cpp.json` y el paso `download`), `engines/test_installer.py::test_ac1_checksum_mismatch` y `llm/test_models.py`.
- **GREEN**: el paso `download` en `engines/installer.py`, `engines/recipes/llama-cpp.json` y `llm/models.py`.
- **REFACTOR**: ninguno.

#### Ciclo 2: cliente y validador [AC-3]

- **RED**: `llm/test_client.py` (servidor falso: válido, inválido y válido, dos inválidos y timeout) y `llm/test_schema.py` (el validador mínimo).
- **GREEN**: `llm/client.py` y `llm/schema.py`.
- **REFACTOR**: ninguno.

#### Ciclo 3: runtime y worker [AC-2]

- **RED**: `llm/test_runtime.py` (comando de arranque por modelo, espera de `/health` y `stop`) y `jobs/test_worker_llm.py`.
- **GREEN**: `llm/runtime.py` y el manejo de LLM caliente en `jobs/worker.py` (apagar antes de otro trabajo de GPU y el tiempo de espera).
- **REFACTOR**: si `worker.py` se acerca a 300 líneas, el ciclo de vida del LLM va a `jobs/llm_warm.py`.

#### Ciclo 4: tareas de texto [AC-4, AC-7]

- **RED**: `llm/tasks/test_script_review.py` y `llm/tasks/test_music_caption.py` (modelo falso).
- **GREEN**: `llm/tasks/{script_review,music_caption}.py`, `llm/prompts/{script_review,music_caption}.md` (las reglas se inyectan desde `formato-guion.md` y las recomendaciones de ACE-Step desde `styles.py`), `llm/prompts.py` (carga y reemplazo de `{{var}}`) y `services/llm_*.py` con sus líneas en `SERVICES`.
- **REFACTOR**: ninguno.

#### Ciclo 5: tareas de subtítulos [AC-5, AC-6]

- **RED**: `llm/tasks/test_subtitles_{translate,correct,keywords}.py`.
- **GREEN**: las tres tareas y sus prompts, el paso de `tracks.en` a `tracks[<lang>]` en `subtitles/document.py` (con migración del documento al cargarlo: un `en` viejo pasa a `tracks["en"]`), `subtitles/languages.py` y `subtitles.glossary`.
- **REFACTOR**: la reubicación de tiempos con `difflib` se comparte con `subtitles/sources.py` (alineación de la 014).

#### Ciclo 6: publicar [AC-8]

- **RED**: `llm/tasks/test_publish.py` (límites por plataforma, capítulos y redondeo a segmentos) y la migración 7 en `test_schema.py`.
- **GREEN**: `llm/tasks/publish.py`, `llm/platforms.json`, `llm/prompts/publish.md`, la migración 7 (`publish_path`) y `GET /library/{id}/publish`.
- **REFACTOR**: ninguno.

#### Ciclo 7: client [AC-9]

- **RED**: `features/settings/AssistantSettings.test.tsx`, `shared/components/LlmModelSelect.test.tsx`, `features/narration/ScriptReviewDiff.test.tsx`, `features/subtitles/{TranslateDialog,CorrectDiff,KeywordSuggest}.test.tsx`, `features/music/DescribeMusic.test.tsx` y `features/library/PublishTab.test.tsx`.
- **GREEN**: los componentes, `shared/components/molecules/UITextDiff/` (diff por palabra, reusado), la tarjeta de Motores, el indicador «Asistente cargado» en la cola y las claves `llm.*` en `es.json`.
- **REFACTOR**: ninguno.

#### Ciclo 8: prueba de modelos, e2e y docs [AC-10]

- **RED**: `devtools/tests/unit/test_llm_eval.py` (los chequeos por caso y el informe, con la API simulada) y los e2e `narration/happy-ai-review`, `subtitles/happy-ai-translate`, `subtitles/happy-ai-correct-glossary`, `music/happy-describe`, `library/happy-publish` y `settings/neg-assistant-off`.
- **GREEN**: `devtools/llm_eval.py`, `tests/llm_eval/cases.jsonl` (los 50 casos), las respuestas grabadas en `_api/llm/` y D-7.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/llm/{models,client,schema,runtime,prompts}.py`, `llm/platforms.json`, `llm/prompts/*.md`, `llm/tasks/*.py` | `unit` |
| Crear | `engines/recipes/llama-cpp.json`, `services/llm_*.py`, `subtitles/languages.py` | `unit` |
| Modificar | `engines/installer.py` (paso `download`), `jobs/worker.py`, `subtitles/document.py`, `db/schema.py` (migración 7), `api/routes/{library,engines}.py`, `services/registry.py`, `cli/main.py`, `messages/{es,en,pt}.json` | `unit` |
| Crear | `devtools/llm_eval.py`, `tests/llm_eval/cases.jsonl` | `uv run pytest devtools -q` |
| Crear | los componentes de D-5 y `shared/components/{LlmModelSelect,TextDiff}.tsx` | `client-unit` |
| Modificar | `features/{narration,subtitles,music,library,settings,engines,queue}/*`, `messages/{es,en,pt}.json` | `client-unit`, `budget` |
| Crear | `tests/e2e/**/happy-ai-*.e2e.ts`, `_api/llm/*` | `e2e` |
| Modificar | `AGENTS.md`, `stack.md`, `devtools.md` (`llm-eval`), `formato-guion.md`, `docs/process/01-done/` (+ `llm.md`) | `agent-context`, `rules` |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Receta y modelos | AC-1 | — | `unit` | [x] |
| T2 | Cliente y validador | AC-3 | — | `unit` | [x] |
| T3 | Runtime y worker | AC-2 | T1, T2 | `unit` | [x] |
| T4 | Tareas de texto | AC-4, AC-7 | T2 | `unit` | [x] |
| T5 | Tareas de subtítulos | AC-5, AC-6 | T2 | `unit` | [x] |
| T6 | Publicar | AC-8 | T2 | `unit` | [x] |
| T7 | Client | AC-9 | T3–T6 | `client-unit` | [x] |
| T8 | Prueba de modelos, e2e y docs | AC-10 | T7 | `e2e`, `devtools` | [x] |
| T9 | Corridas reales y ★ | AC-10, AC-11 | T8 | verificación final | [x] |

## 4. Commits

1. `feat: receta de llama.cpp con descarga verificada y catálogo de modelos LLM` (T1).
2. `feat: cliente LLM con JSON schema y validación` (T2).
3. `feat: llama-server bajo demanda que respeta el turno de la GPU` (T3).
4. `feat: revisar guion y describir música con el LLM local` (T4).
5. `feat: traducir, corregir y sugerir palabras clave en subtítulos con el LLM` (T5).
6. `feat: títulos, descripción, hashtags y capítulos para publicar` (T6).
7. `feat: botones de IA en Narración, Subtítulos, Música y Biblioteca, y ajustes del asistente` (T7).
8. `chore: devtools llm-eval para comparar modelos en español; e2e y docs` (T8 y las fichas).
9. `chore: fijar el modelo recomendado con el resultado de llm-eval` (T9).
