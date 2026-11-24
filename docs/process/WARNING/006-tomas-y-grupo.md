# 006: las tomas de un mismo texto se agrupan con una clave que hereda la regeneración

- **Contexto**: Comparar necesita reunir las tomas del mismo texto (D-4). La clave tiene que salir del trabajo y no de la UI, y una toma regenerada debe quedar en el grupo de su original.
- **Elegida**: `group_key = 'narration:' + sha1(texto con los espacios normalizados)[:12]`. Un archivo de un solo guion cuenta por su contenido, así que un `.txt` y el mismo texto escrito en la UI comparten grupo; un trabajo sobre varios archivos no tiene grupo. `prepare` del servicio de regeneración copia la clave del trabajo de origen. `starred` se marca con una sola sentencia (`CASE WHEN id = ?`), atómica en autocommit. Sin grupo, marcar solo marca esa toma.
- **Descartadas**: una clave por fecha o por id (no une las tomas del mismo texto); el hash del texto sin normalizar (una coma de más separaría las tomas); una tabla de grupos aparte (una columna basta, KISS).
- **Cómo revertir**: quitar `group_key` de `services/narration.py` y el gancho `prepare` de la cola; las tomas quedan sin grupo.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/services/test_narration.py server/tests/unit/src/content_studio/services/test_narration_regenerate.py server/tests/unit/src/content_studio/api/routes/test_jobs.py` (AC-5 y la herencia de la clave al regenerar y al reintentar).
