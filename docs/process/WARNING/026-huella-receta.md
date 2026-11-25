# 026: la huella de la receta decide `outdated` y «Actualizar» reconstruye el motor

- **Contexto**: la instalación solo comparaba `recipe_version` (un número que hay que subir a mano). Cambiar pins o revisiones sin subirlo dejaba a los usuarios con venvs viejos sin aviso. Además, los pasos ya hechos (`steps/<versión>-<n>.done`) impedían volver a correr una descarga cuyo revisión cambió.
- **Elegida**: `load()` calcula el sha256 de los bytes del JSON (`Recipe.sha256`); la instalación lo guarda en `install.json` como `recipe_sha256`. `list_engines` marca `outdated` un motor instalado cuya huella no coincide, también si el manifiesto no tiene huella (instalación anterior). Una reinstalación con otra huella reconstruye el venv y borra todos los marcadores de pasos, así las descargas con revisión nueva se vuelven a bajar. «Actualizar» en Motores llama a `POST /engines/{name}/install`.
- **Descartadas**: comparar solo `recipe_version` (no detecta cambios sin subir el número); reinstalar al actualizar la app (borra gigabytes sin preguntar, datos del usuario); marcar `outdated` en `verification.py` (mide la salud del motor, no la receta).
- **Cómo revertir**: quitar `recipe_sha256` de `install()` y de `list_engines()`, y el campo `sha256` de `Recipe` (commit de la fase 1).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/engines -q` (incluye `test_ac3_receta_cambiada_queda_outdated` y `test_ac3_install_of_an_outdated_engine_reruns_every_step`) y `bun run --cwd client test` (`EngineCard`, AC-7).
- **Pendiente**: ninguno.
