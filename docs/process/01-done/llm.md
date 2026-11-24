---
modulo: asistente
actualizada: 2026-11-24
---

# Asistente (LLM local)

## Qué resuelve

Sugerencias con un LLM local que el usuario acepta o descarta: revisar el guion, traducir y corregir subtítulos, describir la música en español y preparar la publicación de un video. Nada cambia sin que el usuario lo acepte.

## Qué hace hoy

- Runtime: `llama-server` de llama.cpp (`b12676`, CUDA 12.4), con la receta `llama-cpp` y un GGUF Q4_K_M por modelo: `qwen3.5-9b` (★) y `gemma-4-e4b`, los dos Apache 2.0, con el thinking apagado (`enable_thinking: false`; Gemma 4 E4B piensa aunque el sistema no lleve `<|think|>`). Se instalan desde Motores (grupo «Asistente»).
- Cola: trabajos `llm.<tarea>` con recurso `gpu`. El worker arranca `llama-server` con la primera tarea y lo apaga antes de otro trabajo de GPU. Tras una tarea lo deja caliente, con el turno, hasta `llm.idle_seconds` (2 min).
- Cliente HTTP con JSON schema y validación en código: un reintento con el error, y si no, `llm_invalid_output`, con lo que falló en el log del trabajo.
- Tareas:
  - `script_review`: descarta lo que empeora el lint, deja cifras o cambia la idea.
  - `music_caption`: tonalidades del catálogo, 30–300 BPM y «no vocals».
  - `subtitles_translate` (la pista se exporta como `<id>-<nombre>.<idioma>.srt` y se elige en el selector «Pista»), `subtitles_correct` (glosario, conserva los tiempos) y `subtitles_keywords` (la palabra manda sobre el índice y debe tener contenido).
  - `publish`: límites por plataforma (la descripción se corta en una oración si se pasa) y capítulos de YouTube en `m:ss`, llevados al inicio de un segmento real.
- UI: «Revisar con IA» (diff por párrafo), «Describir en español», herramientas del editor de subtítulos, «Publicar» en el detalle de la Biblioteca, Ajustes > Asistente e indicador en la cola. Con el asistente apagado no aparece ningún botón de IA.
- CLI: `studio llm script-review|music-caption`. Comparar modelos: `python -m devtools llm-eval`, sobre 50 casos en español.

## Dónde vive

- `server/src/content_studio/llm/` (`models`, `client`, `schema`, `runtime`, `prompts/`, `tasks/`, `task_main`), `jobs/llm_warm.py`, `api/routes/llm.py` y `services/llm_task.py`.
- `client/src/features/assistant/` y los componentes de cada sección; `devtools/llm_eval.py` y `tests/llm_eval/cases.jsonl`.

## Rendimiento medido (24/11/2026, RTX 4060 Laptop de 8 GB, ★ Qwen3.5 9B)

| Tarea | Tiempo, con la carga | Datos |
| :--- | ---: | :--- |
| Describir música | 6 s | una descripción |
| Revisar guion | 24 s | 4 párrafos |
| Traducir subtítulos | 30 s | 42 cues al portugués |
| Corregir con glosario | 38 s | 42 cues |
| Palabras clave | 40 s | 42 cues |
| Publicar | 31–47 s | YouTube y Reels, video de 2:12 |

Cargar el modelo tarda unos 2 s. VRAM pico 7,8 GB con el escritorio abierto; tras 2 min sin uso el server se apaga y suelta el turno. Antes de un trabajo de GPU (narración o música), el worker lo apaga: nunca hay dos modelos a la vez.

## Historial

- 2026-11-24: asistente local con cuatro funciones y prueba de modelos; ★ Qwen3.5 9B tras apagar el thinking de Gemma (spec 021).
- 2026-11-24: verificación integral (023): «Revisar con IA» descarta los párrafos que quitan tildes.
