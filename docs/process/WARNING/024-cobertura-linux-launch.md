# 024: `app_check/launch.py` queda bajo el 80 % solo en Linux y entra al baseline de cobertura

- **Contexto**: en la CI de Linux (`calidad`, 3.10 y 3.12), `devtools/app_check/launch.py` mide 62,96 %. El Job Object (`CreateJobObjectW`, `AssignProcessToJobObject`, `NtResumeProcess`) y `process_alive` con `OpenProcess` solo corren en Windows, igual que `gpu_lock.py` (`004-cobertura-linux-gpu-lock`). En Windows la etapa `unit` pasa, con la prueba real del Job (`test_ac6_real_job_kills_only_its_tree`).
- **Elegida**: agregar `devtools/app_check/launch.py` a `tests/validators/coverage.baseline.json`, como en la 004. El 80 % no se baja.
- **Descartadas**: `# pragma: no cover` en las ramas de Windows (esconde código que sí corre); simular `ctypes` en Linux (prueba el mock, no el Job); un módulo aparte solo para la medición (la 004 descartó lo mismo).
- **Cómo revertir**: quitar la línea del baseline cuando las ramas de Windows tengan una prueba que corra en Linux.
- **Cómo comprobarla**: `calidad` en verde en 3.10 y 3.12 (`gh pr checks`), y `python -m devtools test-runner --type=unit --files=devtools/app_check/launch.py` en Windows.
