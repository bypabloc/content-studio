# 030: el message de los recibos va en el idioma de la interfaz

- **Qué**: 02 §3 pide que `message` del recibo de error vaya en el idioma de `ui.locale`. Hoy lleva el texto crudo del worker o el código.
- **Por qué no se hizo**: los textos del catálogo se resuelven en la API con `Accept-Language`; el sondeo no tiene idioma. Falta decidir de dónde sale `ui.locale` para el sondeo.
- **Cuándo**: en la fase 2, con la API de carpetas.
- **Quién**: agente.
- **Qué lo cierra**: un test en `test_receipts.py` que compare `message` con el catálogo en el idioma de `ui.locale`.
