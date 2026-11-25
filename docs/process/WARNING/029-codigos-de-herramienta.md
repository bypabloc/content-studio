# 029: los códigos de error de las herramientas van al catálogo y al validador se declaran

- **Contexto**: `etapa i18n` solo ve los códigos de `ApiError` y los diccionarios `{'code': …}`. Las herramientas lanzan
  `ToolError('input_not_found')` y el puente arma `error.{code}`, así que sus claves salían como «no usadas» y, sin
  texto, el agente recibía el código crudo (`narration_source`).
- **Elegida**: los seis códigos y `validation_failed` tienen texto en `es`, `en` y `pt`, y el puente traduce todos
  (sin `TEXT_CODES`). Los seis códigos que el validador no ve se declaran en `tests/validators/i18n.json` como
  `dynamicPrefixes`, igual que `error.disk_full`.
- **Descartadas**: usar `ApiError` en el puente (no es un error de la API, y la forma sería engañosa); dejar los códigos
  sin texto.
- **Cómo revertir**: quitar esas claves de los tres catálogos y de `dynamicPrefixes`; volver a `TEXT_CODES`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=i18n`.
