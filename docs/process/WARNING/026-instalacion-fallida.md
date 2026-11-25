# 026: un intento de instalación fallido hace que la siguiente reutilice pasos y venv de la receta anterior

- **Contexto**: `installer.install()` solo considera `stale` a un motor con `install.json` y otra huella. Tras un intento fallido solo queda `installing.json`, y los marcadores `steps/<version>-<n>.done` se nombran por `recipe.version`, no por la huella. Con heartmula, la receta corregida (misma versión) saltó venv y pip del intento fallido: el venv seguía en 3.14 y con la pyarrow de la receta vieja.
- **Elegida**: para esta spec, limpiar a mano la carpeta del motor de prueba (`tmp/spec-026/e/heartmula`) y reinstalar. El fallo queda como corrección pendiente del instalador (fase 1 de la spec), con su test.
- **Descartadas**: dejar el instalador como está (un usuario con un intento fallido y una receta nueva quedaría con el venv viejo, justo el caso de «Actualizar»); corregirlo sin test.
- **Cómo revertir**: no aplica (es una corrección pendiente, no un cambio).
- **Cómo comprobarla**: test RED: instalar con una receta que falle en un paso pip, corregir la receta (misma versión) y reinstalar; el venv debe reconstruirse con los pasos nuevos. El test iría en `server/tests/unit/src/content_studio/engines/test_installer.py`.
- **Pendiente**: la corrección del instalador en esta spec, antes del PR.
