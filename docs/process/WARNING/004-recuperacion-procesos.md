# 004: al arrancar, el server interrumpe solo los trabajos cuyo proceso ya no existe

- **Contexto**: `Worker.start()` marcaba como `interrupted` todo lo `running` (AC-11). La CLI corre sus trabajos en su propio proceso y la base es compartida: al arrancar el server, un trabajo de la CLI que seguía corriendo pasó a `error` (job 2 en la verificación) y la CLI lo cerró después como `done`, con el `error_code` heredado.
- **Elegida**: la columna `owner_pid` (migración 2) guarda el pid que reclama el trabajo. Al arrancar se interrumpe solo lo cuyo dueño murió, o lo que no tiene dueño (trabajos anteriores a la migración). En Windows se pregunta a `OpenProcess`; en POSIX, `os.kill(pid, 0)`. En Windows no se usa `os.kill`, porque termina el proceso.
- **Descartadas**: interrumpir por antigüedad (un trabajo largo y sano se marcaría); un archivo de lock por trabajo (más piezas para el mismo resultado); no recuperar nada (se rompe AC-11).
- **Cómo revertir**: volver a `UPDATE jobs SET status = 'error' ... WHERE status = 'running'` en `recover_interrupted` y quitar `_alive`. La columna de la migración 2 queda sin uso.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/jobs/test_queue.py -k recover`. En la verificación real, un trabajo de la CLI en curso sobrevivió al reinicio del server (job 10).
- **Antes de `main`**: la rama POSIX de `_alive` no corrió en Windows; correr `test_queue.py` en WSL.
