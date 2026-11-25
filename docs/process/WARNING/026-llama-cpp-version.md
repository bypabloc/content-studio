# 026: llama.cpp b12686 en lugar de b12676 (la salida del asistente no empeora)

- **Contexto**: el release b12686 (2026-11-24) trae builds CUDA 12.4 para Windows. La receta anterior fijaba b12676. D-4 pide el último que funcione y que no empeore la salida.
- **Elegida**: b12686 (zip de 358 MB, sha256 `7aeb4f0e`, cudart 12.4 sin cambio, sha `8c79a9b2`). Evaluación de 50 casos con gemma-4-e4b y qwen3.5-9b (`devtools llm-eval`): script_review gemma 94,7 % (b12676: 90,7 %) y qwen 97,3 % (96,0 %); traducciones al 100 % en ambos.
- **Descartadas**: b12676 (la salida empeora en los dos modelos).
- **Cómo revertir**: cambiar la URL y el sha256 de los dos pasos `download` de `llama-cpp.json` a b12676 (`1d5692d9`) y reinstalar el motor.
- **Cómo comprobarla**: `uv run python -m devtools llm-eval --models gemma-4-e4b qwen3.5-9b` y comparar `report.md`.
- **Pendiente**: [026-llm-casos-fallidos](../PENDING/026-llm-casos-fallidos.md): en script_review falla 1 de 25 casos en cada modelo.
