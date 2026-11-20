# 006: narrate() no importa torch; el pico de VRAM sale de una función aparte

- **Contexto**: `narrate()` importaba `torch` al entrar, solo para imprimir el pico de VRAM al final. El ciclo 3 del plan supone que el pipeline se prueba sustituyendo `fix()`, pero el import va antes y el test fallaba con `ModuleNotFoundError: No module named 'torch'` en el venv del server, que no tiene GPU ni torch.
- **Elegida**: el pico lo da `peak_vram_gib()`, que importa `torch` solo cuando se llama. `narrate()` ya no lo importa. Las pruebas sustituyen `pipeline.fix` y `pipeline.peak_vram_gib`. La salida de la CLI no cambia.
- **Descartadas**: añadir `torch` al grupo `dev` (pesa varios GB en el venv del server y la spec no lo pide); `pytest.importorskip('torch')` (el AC-2 quedaría sin verificar en la CI); importar `torch` a nivel de módulo (rompería `--help` y el catálogo sin el venv del motor, `codigo-python.md`).
- **Cómo revertir**: volver `import torch` al inicio de `narrate()` y quitar `peak_vram_gib()`. El test de AC-2 dejaría de correr en el venv del server.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/narration/test_pipeline.py` pasa sin torch instalado. En el RED del ciclo se vio el `ModuleNotFoundError` antes del cambio.
