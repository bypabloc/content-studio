# 012: versiones de las recetas de motores

- **Contexto**. Algunos números de versión de los README corresponden a una instalación anterior. Se pudieron consultar los paquetes, commits y revisiones de modelos de la instalación de Windows sin cargar motores.
- **Elegida**. Las recetas fijan los paquetes directos, los commits de los repositorios locales y las revisiones de pesos de la caché. Los pasos con rutas relativas comparten la raíz de la familia del motor. Los tamaños son estimaciones de venv y pesos. La compatibilidad con CPU de VoxCPM2 y CosyVoice se basa en el código de los motores.
- **Descartadas**. Los comandos de instalación con versiones abiertas podrían resolver paquetes diferentes. Las revisiones `main` de los pesos pueden cambiar sin que se modifique la receta.
- **Cómo revertir**. Revierte el grupo de recetas o cambia el archivo del motor y su versión de receta antes de instalarlo otra vez.
- **Cómo comprobarla**. `uv run pytest server/tests/unit/src/content_studio/engines/test_recipes.py -q` verifica las nueve recetas. La instalación y el humo de Qwen 0.6B se comprobarán en la verificación final.
