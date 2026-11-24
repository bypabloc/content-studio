# 021: build de llama.cpp fijado

- **Contexto**: el asistente usa `llama-server` del release oficial de `ggml-org/llama.cpp` para Windows con CUDA (D-1). La receta `engines/recipes/llama-cpp.json` baja dos zips y comprueba su sha256 antes de extraerlos (paso `download`, nuevo en la 021).
- **Elegida**: build `b12676` (2026-11-24), variante CUDA 12.4 x64: `llama-b12676-bin-win-cuda-12.4-x64.zip` (sha256 `1d5692d9…ddb84`) y `cudart-llama-bin-win-cuda-12.4-x64.zip` (sha256 `8c79a9b2…ae1d6`), con los digests del API de GitHub. CUDA 12.4 funciona con el driver 621.24 de este equipo y con drivers más viejos que la 13.5.
- **Descartadas**: CUDA 13.5 (exige un driver más nuevo, sin ventaja para una RTX 4060); Vulkan (más lento en NVIDIA); compilar desde la fuente (CUDA Toolkit y MSVC en el equipo del usuario).
- **Cómo revertir**: cambiar las dos URL y sus sha256 en `llama-cpp.json` y subir `version` en la receta.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/engines` y, con la receta instalada, `llama-server.exe --version` (el paso `verify`).
- **Pendiente**: ninguna.
