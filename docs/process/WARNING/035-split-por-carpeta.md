# 035: diarize.split recibe la carpeta de turnos y corta por turnos exclusivos

- **Contexto**: el diseño pedía `{job: <id>}` con el error `job_not_found`. `validate` del servicio no consulta la base, igual que `clean.render`, que recibe la carpeta de su análisis. Cortar con los turnos normales dejaría voz de otro hablante en los solapes.
- **Elegida**: `{input, turns}`, con `turns` la carpeta que tiene `turns.json`. El corte usa `exclusive_diarization`: en cada instante suena un solo hablante (la tabla «debe sonar» de AC-5).
- **Descartadas**: resolver el id del trabajo dentro de `validate` (obliga al servicio a abrir la base); cortar con `diarization` (deja los solapes).
- **Cómo revertir**: `services/diarize_split.py` y la acción `split` de `diarization/job_main.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/diarization/test_job_main.py -q` (con ffmpeg real).
- **Pendiente**: la escucha de los solapes en la verificación final de la 035.
