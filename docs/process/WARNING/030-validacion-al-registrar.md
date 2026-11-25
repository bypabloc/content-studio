# 030: el registro valida los parámetros con la carpeta como entrada de prueba

- **Contexto**: 02 §2 pide 422 con los errores de `validate` al registrar. Algunos `validate` miran la entrada, y al registrar todavía no hay archivo.
- **Elegida**: `store.register` pasa la carpeta como valor del parámetro de entrada (`inputs.INPUT_PARAM`). Así llegan al registro los errores que no dependen del archivo; el archivo real se valida al encolarlo, y si falla va a `failed/`.
- **Descartadas**: no validar al registrar (la app no sabría que sus parámetros están mal hasta que se suelta un archivo); validar con un archivo de muestra (al registrar no existe).
- **Cómo revertir**: quitar la llamada a `validate` de `store.register`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/inbox/test_store.py`.
