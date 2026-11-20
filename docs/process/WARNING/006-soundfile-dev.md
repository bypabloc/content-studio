# 006: soundfile entra al grupo `dev` del workspace para probar el pipeline sin GPU

- **Contexto**: `narration/pipeline.py` escribe los bloques y la toma con `soundfile`, que hoy solo está en el venv de cada motor. Las pruebas del AC-2 y del AC-3 corren en el venv del server (`uv run pytest`, sin GPU), donde no hay `soundfile` y el import falla antes de probar nada.
- **Elegida**: `soundfile` en el grupo `dev` de la raíz (`pyproject.toml`), junto a `numpy`, que el mismo pipeline ya necesita en las pruebas. `torch` no entra: `fix()` se sustituye en la prueba, porque lo que se prueba es dónde se guardan los bloques, no la semilla de la GPU.
- **Descartadas**: `pytest.importorskip('soundfile')` (el AC-2 quedaría sin verificar en la CI); escribir los WAV con el módulo `wave` (no hace flotantes de 32 bits, y el AC-3 compara bytes de los bloques); poner `soundfile` en el grupo `legacy` (es de la narración, no de los tests).
- **Cómo revertir**: quitar la línea de `pyproject.toml` y `uv lock`; el pipeline seguiría funcionando en el venv del motor, y las pruebas de AC-2 y AC-3 dejarían de correr.
- **Cómo comprobarla**: `uv run python -c "import soundfile"` sin error, y `uv run pytest server/tests/unit/src/content_studio/narration/test_pipeline.py`.
- **Antes de**: el merge a `dev`.
