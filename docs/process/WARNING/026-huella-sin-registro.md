# 026: los motores instalados antes de la huella salen outdated una vez

- **Contexto**: `engines/installer.py:245` compara `recipe_sha256` del `install.json` con la receta. Los registros anteriores a F1 no tienen esa clave (p. ej. faster-whisper, instalado el 22-nov). Sin huella, el estado sale `outdated`. Verificado sin escribir nada: faster-whisper, gemma-4-e4b, llama-cpp, qwen3.5-9b y vision salen `OUTDATED` en la base real.
- **Elegida**: dejarlo así. Una instalación sin huella no prueba que su receta sea la actual; marcarla como al día ocultaría cambios reales.
- **Descartadas**: marcar como actual lo que no tiene huella; reinstalar solos al actualizar (la spec lo prohíbe: borra y baja GB sin preguntar).
- **Costo para el usuario**: un «Actualizar» por motor gestionado. Ese botón reconstruye el motor y rehace sus descargas (faster-whisper, gemma, llama-cpp, qwen3.5-9b y vision).
- **Cómo revertir**: no aplica. Desaparece con el primer «Actualizar» de cada motor, que escribe la huella nueva.
- **Cómo comprobarla**: `uv run python tmp/spec-026/check-outdated.py` (solo lectura).
