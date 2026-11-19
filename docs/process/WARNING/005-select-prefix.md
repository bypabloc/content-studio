# 005: las elecciones de los selectores van bajo `select.` y el restablecer solo borra ese prefijo

- **Contexto**: «Restablecer elecciones» tiene que borrar las preferencias de los selectores y dejar el tema (`ui.*`) y los avisos (`notify.*`). Sin un prefijo común, habría que listar las claves de cada sección.
- **Elegida**: cada selector guarda su elección con una clave `select.<seccion>.<campo>` (`RecommendedSelect` recibe `settingKey`). `DELETE /settings?prefix=select.` borra solo esas claves y responde 422 con cualquier otro prefijo (`server/src/content_studio/api/routes/settings.py`).
- **Descartadas**: lista de claves a borrar en el cliente (cada sección nueva debería acordarse de agregarse); borrar todo `settings` (perdería el tema y los avisos); guardar las elecciones en `localStorage` (el CLI no las vería, decisión del lote).
- **Cómo revertir**: cambiar `SELECTOR_PREFIX` y el prefijo del cliente (`SettingsPage.tsx`) en el mismo commit; las claves guardadas no cambian de nombre sola.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_settings.py` (borra solo `select.*`) y `cd client && bun run test` (`SettingsPage.test.tsx`).
- **Antes de**: el merge a `dev`.
