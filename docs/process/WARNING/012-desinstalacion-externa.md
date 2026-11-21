# 012: `force` desinstala solo el venv externo conocido

- **Contexto**. Las instalaciones externas no tienen `install.json`; sus modelos pueden compartir caché y el checkout contiene referencias y voces del usuario.
- **Elegida**. Con `force` explícito, se elimina únicamente el venv indicado por la receta, si resuelve como hijo directo de `narration/` o `music/` y conserva el nombre esperado. Las cachés, referencias, voces, salidas y demás archivos quedan intactos. Para instalaciones `app`, `force` no amplía las rutas aceptadas por el manifiesto.
- **Descartadas**. Inferir y borrar repositorios o pesos externos puede eliminar modelos compartidos o datos ajenos. Permitir que `force` ignore las rutas del manifiesto rompe el límite de propiedad.
- **Cómo revertir**. Revierte el commit de soporte a `force`; las instalaciones externas volverán a responder `engine_external`.
- **Cómo comprobarla**. `uv run pytest server/tests/unit/src/content_studio/engines/test_installer.py server/tests/unit/src/content_studio/api/routes/test_engines.py -q` prueba el venv temporal y confirma que se preservan referencias y caché.
- **Pendiente**. Ninguna.
