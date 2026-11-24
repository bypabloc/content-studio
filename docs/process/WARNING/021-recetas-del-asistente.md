# 021: una receta por modelo del asistente

- **Contexto**: Motores instala, verifica y desinstala por receta (012). La spec pide la tarjeta «Asistente (llama.cpp)» con el runtime y los dos modelos, cada uno instalable por separado.
- **Elegida**: tres recetas de la familia `assistant`: `llama-cpp` (los zips del release), `gemma-4-e4b` y `qwen3.5-9b` (un paso `hf` con solo su GGUF Q4_K_M y la revisión fijada). La tarjeta las agrupa por familia. Cada receta de modelo trae un venv mínimo con `huggingface-hub`, porque el paso `hf` corre en el venv del motor; `llama-cpp` deja un venv vacío, porque toda receta lo exige.
- **Descartadas**: una sola receta con runtime y modelos (11 GB de golpe, sin poder elegir un modelo); descargar el modelo la primera vez que se usa, como whisper (5 GB dentro de un trabajo de la cola, sin la tarjeta de Motores).
- **Cómo revertir**: borrar las dos recetas de modelos y sumar sus pasos `hf` a `llama-cpp.json`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/llm/test_models.py` (recetas y catálogo coinciden).
- **Pendiente**: la VRAM de cada modelo en la receta es una estimación hasta medirla en la verificación final.
