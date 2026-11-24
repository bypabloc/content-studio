# 012: las instalaciones externas siguen disponibles en desarrollo

- **Contexto**. Los venvs, repositorios y pesos que ya existen en el checkout pertenecen al usuario. Varios venvs editables tienen referencias absolutas a su repositorio.
- **Elegida**. En desarrollo, el motor usa primero su venv administrado y luego la instalación externa del checkout. Conserva juntos el venv, el código y los pesos de cada instalación. Las referencias, las voces construidas y las muestras del checkout siguen disponibles en desarrollo. El modo instalado usa su carpeta de datos de usuario.
- **Descartadas**. Una migración automática habría movido datos existentes y podría haber roto los venvs. Un único directorio de pesos para motores administrados y externos podría descargar modelos de nuevo.
- **Cómo revertir**. Revierte el commit de rutas dinámicas. Los datos de las instalaciones externas conservan sus rutas.
- **Cómo comprobarla**. Ejecuta `uv run pytest server/tests/unit/src/content_studio/test_paths.py -q`. Para revisar los venvs existentes, usa la batería local y el turno de GPU de la spec 012.
