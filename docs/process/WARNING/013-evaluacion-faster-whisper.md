# 013: la evaluación y el chequeo de tomas usan faster-whisper, con tres desvíos de D-7

- **Contexto**: `narration --evaluate` y el chequeo de tomas llamaban al comando `whisper` (openai-whisper) con el modelo `medium` fijo. D-7 pide que usen el servicio de faster-whisper (D-2) con el modelo de Ajustes, y que no quede `shutil.which('whisper')` (AC-10).
- **Elegida**:
  - Un proceso del servicio por audio (`transcribe_main.transcribe_text`), que corre en el venv de faster-whisper. Así no hace falta importar faster-whisper en el proceso de la narración ni en el de la toma.
  - El modelo sale de la preferencia que escribe el selector del cliente, `select.whisper.model` (el mismo que usa el limpiador), con large-v3-turbo (★) por defecto. Lo lee `transcription.models.selected`.
  - La evaluación de una narración pasa a large-v3-turbo; antes era `medium`.
- **Descartadas**:
  - La clave `transcription.model` de D-7: el selector de la UI ya escribe `select.whisper.model`, y crear una segunda clave haría que Ajustes y la evaluación no coincidieran.
  - Un proceso por lote de audios: exigiría cambiar el CLI del servicio (`--input` de varios archivos) y su contrato de API. Se acepta el coste de cargar el modelo una vez por párrafo.
  - Mantener `medium` en la evaluación: D-7 pide el modelo de Ajustes y large-v3-turbo es el recomendado.
- **Cómo revertir**: el commit de T8 (`refactor: evaluación y chequeo de tomas con faster-whisper`). Restaurar `shutil.which('whisper')` y `WHISPER_MODEL = 'medium'` en `narration/evaluation/review.py` y `services/voice_check.py`.
- **Cómo comprobarla**: `uv run pytest tests/validators/test_structure.py::test_ac10_no_whisper_cli` (sin `whisper` en `server/src`) y `uv run pytest server/tests/unit/src/content_studio/transcription/test_models.py server/tests/unit/src/content_studio/narration/evaluation/test_review.py`. La corrida real con `uv run studio narration tts --evaluate` queda para la verificación final (T9).
- **Pendiente**: [PENDING 013-receta-cosyvoice](../PENDING/013-receta-cosyvoice.md). La receta de CosyVoice sigue instalando `openai-whisper`; no se comprobó si CosyVoice lo importa.
