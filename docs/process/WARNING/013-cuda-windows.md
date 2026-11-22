# 013: faster-whisper en CUDA sobre Windows, con respaldo a CPU

- **Contexto**: el limpiador y la evaluación cargan faster-whisper en el venv `.venv-whisper` de la receta `faster-whisper`. En la RTX 4060 de 8 GB el modelo sale en CUDA; en un equipo sin NVIDIA no hay GPU que usar.
- **Elegida**: `transcribe_main._load_model` usa `device='cuda'` con `compute_type='int8_float16'` si `system.tools.detect()['gpu']` encuentra una GPU; si no, `device='cpu'` con `int8`. Así large-v3-turbo cabe en la VRAM que pide la spec (menos de 3 GB en la transcripción).
- **Descartadas**:
  - `float16` en CUDA: ocupa más VRAM que `int8_float16` y no mejora la transcripción de voz.
  - Forzar CPU siempre: la transcripción de 3 a 5 minutos sería varias veces más lenta.
- **Cómo revertir**: fijar `device`/`compute_type` en `transcription/transcribe_main.py::_load_model`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/transcription/test_transcribe_main.py::test_load_model_uses_cuda_with_a_gpu_and_cpu_without_one` (simulado). La medida real de VRAM pico con `nvidia-smi --query-gpu=memory.used` durante la transcripción es el punto 2.3 de la verificación final (T9). Hasta entonces, esta ficha sigue abierta.
