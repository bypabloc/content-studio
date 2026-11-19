# 017: asistente con LLM local (Gemma 4 E4B y Qwen3.5-9B bajo demanda)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `017-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **El LLM solo propone**: ningún texto, subtítulo ni parámetro cambia sin que el usuario lo acepte. Las pruebas usan `tmp/spec-017/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client) |
| Rama | `feature/017-local-llm-assist` desde `origin/dev`, en `../content-studio-worktrees/017-local-llm-assist/` |
| Depende de | [014](../014-library/README.md), fusionada en `origin/dev`. **Se ejecuta antes de la 015**, que depende de esta |
| Origen | Pedido del usuario y [docs/research/llm-locales/](../../../research/llm-locales/README.md) |

## Objetivo

Un asistente con un LLM local que mejora la salida de cuatro funciones del estudio, siempre como sugerencia aceptable:

1. **Narración**: revisar el guion según las reglas de `formato-guion.md` que el linter no puede arreglar, con un diff por párrafo.
2. **Subtítulos**: traducir a cualquier idioma (whisper solo traduce al inglés) respetando el largo, corregir la transcripción con un glosario y sugerir palabras clave y emojis.
3. **Música**: pasar una descripción en español al caption en inglés de ACE-Step, con tonalidad, BPM y compás.
4. **Publicar**: títulos, descripción, hashtags y capítulos por plataforma a partir de la transcripción.

Los modelos (Gemma 4 E4B ★ y Qwen3.5-9B) y llama.cpp se descargan bajo demanda desde Motores. El ★ se fija con una prueba propia en español.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Runtime: receta de llama.cpp, catálogo de modelos y `llama-server` bajo demanda con el turno de la GPU | PEN |
| 2 | Tareas: prompts, JSON schema y validación posterior | PEN |
| 3 | Client: Revisar guion, Traducir y corregir subtítulos, Describir música y Publicar | PEN |
| 4 | Prueba de modelos en español y ★ con datos propios | PEN |

## Decisiones clave

* D-1: `llama-server` (llama.cpp CUDA de Windows) como proceso hijo, con API compatible con OpenAI y JSON schema. Arranca con la primera petición, toma el turno de la GPU y se apaga a los 2 minutos sin uso.
* D-2: cada tarea es un prompt (en `.md`), un JSON schema y una validación en Python que rechaza o reintenta lo que no cumple. La regla no se le confía al modelo.
* D-3: las peticiones del LLM son trabajos `llm.*` de la cola (recurso `gpu`), y el worker mantiene el servidor caliente entre trabajos `llm.*` seguidos.
* D-4: thinking apagado en los dos modelos, con el muestreo recomendado por cada card.
* D-5: `devtools llm-eval` corre unos 50 segmentos reales con los modelos instalados y deja un informe. El ★ se actualiza con ese resultado.

## WARNING y PENDING

* WARNING: `017-llama-cpp-version.md` (build CUDA fijado y su sha256) y `017-recomendado.md` (resultado de la prueba y el ★ elegido).
* PENDING: `017-vision-miniaturas.md` (usar la visión de Gemma 4 para elegir miniaturas, si el usuario lo pide).
