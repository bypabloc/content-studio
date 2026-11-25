# 030: los recibos se asientan en el sondeo, no suscritos al Broker

- **Contexto**: 02 §4.1 dice «al terminar un trabajo (evento del worker)»; el plan de la fase 1 (C3) decía «suscrito al Broker».
- **Elegida**: `receipts.settle` corre en cada sondeo y mira los archivos en `processing/` cuyo trabajo terminó. Así cubre los trabajos de `studio` (que no pasan por el Broker del server) y los que terminaron con el server apagado. Costo: hasta 2 s de atraso.
- **Descartadas**: suscribirse al Broker (no ve los trabajos de la CLI, y un evento que se pierde en un reinicio no se recupera).
- **Cómo revertir**: suscribir un manejador al Broker en `cli/serve.py` y quitar la llamada a `receipts.settle` de `scan_once`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/inbox/test_receipts.py`.
