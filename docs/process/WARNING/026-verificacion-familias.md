# 026: la verificación de Motores no tiene caso para las familias transcription y vision

- **Contexto**: `engines/verification.py` genera audio (narración, música) o prueba el GGUF (assistant). Para `transcription` (faster-whisper) y `vision` (opencv) devuelve `Unsupported engine family`, así que «Verificar» falla en Motores para esos dos motores. El venv sí importa su librería (su paso `verify` de la receta pasa, y la prueba de la spec lo confirma: YuNet carga y la transcripción sale).
- **Elegida**: no implementar aquí el caso nuevo: es un cambio de `verification.py` de la spec de Motores, no de las recetas, y la spec 026 no lo pide. Queda registrado para que no pase desapercibido.
- **Descartadas**: marcar los motores como verificados a mano; implementar el caso sin prueba (sería un cambio de comportamiento sin spec).
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**: `uv run studio --db <base> engines verify faster-whisper` debe fallar con «Unsupported engine family: transcription» hasta que exista el caso.
- **Pendiente**: caso de verificación para `transcription` y `vision` (ejecutar el `verify` de la receta) en la spec de Motores; ficha de PENDING [026-verificacion-familias](../PENDING/026-verificacion-familias.md).
