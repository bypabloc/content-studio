# 012: el error de espacio insuficiente llega como resultado de un trabajo

- **Contexto**. `disk_full` se produce dentro del proceso instalador y el worker lo devuelve como código del trabajo; no aparece como literal en una llamada a `ApiError`.
- **Elegida**. Registrar `error.disk_full` como uso dinámico en `tests/validators/i18n.json` para que los tres catálogos se validen sin declarar dinámico todo el espacio de errores.
- **Descartadas**. Omitir el mensaje dejaría el código visible como clave. Declarar `error.` entero permitiría claves de error sin traducción ni uso.
- **Cómo revertir**. Revierte la entrada `error.disk_full` del validador y los catálogos asociados si se elimina el código de error.
- **Cómo comprobarla**. `uv run python -m devtools test-runner --type=i18n` valida el uso y la igualdad de los tres mensajes.
- **Pendiente**. Ninguna.
