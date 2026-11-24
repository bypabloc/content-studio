---
modulo: asistente
actualizada: 2026-11-24
---

# Asistente (LLM local)

## Qué resuelve

Sugerencias con un LLM local que el usuario acepta o descarta: revisar el guion, traducir y corregir subtítulos, describir la música en español y preparar la publicación de un video. Nada cambia sin que el usuario lo acepte.

## Qué hace hoy

- Runtime: `llama-server` de llama.cpp (`b12676`, CUDA 12.4), con la receta `llama-cpp` y un GGUF Q4_K_M por modelo: `gemma-4-e4b` (★) y `qwen3.5-9b`, los dos Apache 2.0. Se instalan desde Motores (grupo «Asistente»).
- Cola: trabajos `llm.<tarea>` con recurso `gpu`. El worker arranca `llama-server` con la primera tarea y lo apaga antes de otro trabajo de GPU. Tras una tarea lo deja caliente, con el turno, hasta `llm.idle_seconds` (2 min).
- Cliente HTTP con JSON schema y validación en código: un reintento con el error, y si no, `llm_invalid_output`.
- Tareas:
  - `script_review`: descarta lo que empeora el lint, deja cifras o cambia la idea.
  - `music_caption`: tonalidades del catálogo, 30–300 BPM y «no vocals».
  - `subtitles_translate`, `subtitles_correct` (glosario, conserva los tiempos) y `subtitles_keywords`.
  - `publish`: límites por plataforma y capítulos de YouTube en el inicio de un segmento real.
- UI: «Revisar con IA» (diff por párrafo), «Describir en español», herramientas del editor de subtítulos, «Publicar» en el detalle de la Biblioteca, Ajustes > Asistente e indicador en la cola. Con el asistente apagado no aparece ningún botón de IA.
- CLI: `studio llm script-review|music-caption`. Comparar modelos: `python -m devtools llm-eval`, sobre 50 casos en español.

## Dónde vive

- `server/src/content_studio/llm/` (`models`, `client`, `schema`, `runtime`, `prompts/`, `tasks/`, `task_main`), `jobs/llm_warm.py`, `api/routes/llm.py` y `services/llm_task.py`.
- `client/src/features/assistant/` y los componentes de cada sección; `devtools/llm_eval.py` y `tests/llm_eval/cases.jsonl`.

## Historial

- 2026-11-24: asistente local con cuatro funciones y prueba de modelos (spec 021).
