# 004: gpu_lock.py queda bajo el 80 % solo en Linux y entra al baseline de cobertura

- **Contexto**: en la CI de Linux (`calidad`, 3.10 y 3.12) `gpu_lock.py` mide 75,38 %. Las ramas de Windows (`OpenProcess`, `GetExitCodeProcess`, `CloseHandle`) no se ejecutan en Linux, igual que pasó con los módulos de `cli` y `common` de la 003 (ver `003-cobertura-ci`).
- **Elegida**: añadir `server/src/content_studio/gpu_lock.py` a `tests/validators/coverage.baseline.json`, con 75,38 % en el mensaje del commit. Es el procedimiento de la 003: el 80 % no se baja, y el archivo sale del baseline cuando sus ramas de Windows tengan prueba en Linux o se separen.
- **Descartadas**: `# pragma: no cover` en las ramas de Windows (esconde código que sí corre en Windows); moverlas a un módulo aparte solo para la medición (una pieza más sin ganancia real).
- **Cómo revertir**: quitar la línea de `coverage.baseline.json` y cubrir las ramas de Windows con una prueba que no dependa de la plataforma.
- **Cómo comprobarla**: `calidad` en verde en 3.10 y 3.12 (`gh pr checks`).
- **Pendiente**: ninguno; la ficha se borra al aplicar la reversión.
