# 030: un trabajo cancelado va a failed/ con el código cancelled

- **Contexto**: 02 §3 solo define `done/` y `failed/`. El worker deja el trabajo en `cancelled` cuando alguien lo cancela.
- **Elegida**: `failed/<nombre>/` con `<nombre>.error.json` y `code` igual a `cancelled`. El original no se pierde y la app sabe que no hay salida.
- **Descartadas**: dejar el archivo en `processing/` (quedaría ahí para siempre); devolverlo a la carpeta (la siguiente vuelta lo reprocesaría).
- **Cómo revertir**: quitar `cancelled` de `FINISHED` en `inbox/receipts.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/inbox/test_receipts.py::test_cancelled_goes_to_failed_with_its_own_code`.
