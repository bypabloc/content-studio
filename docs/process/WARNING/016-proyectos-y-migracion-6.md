# 016: la tabla `mix_projects` es la migración 6, y los tramos de voz llegan con la caché o al consultar

- **Contexto**: la spec pide la migración 5, pero 014 ya la ocupó (`subtitle_projects`); la 4 es la caché de la 013. Los tramos de voz salen de la caché de transcripciones, que solo guarda `clean.analyze` y `subtitles.create`: un `transcribe` suelto no la llena.
- **Elegida**:
  - Migración 6 (`mix_projects`: id, nombre, ruta del `mix.json` y fechas; ningún BLOB).
  - `POST /mix/prepare`: con caché, los tramos salen al momento; sin caché, encola un `transcribe` y guarda su id en el `mix.json`.
  - `GET /mix/{id}` (y `/curve`) completa los tramos cuando ese trabajo termina: lee su `words.json`, lo registra en la caché y guarda los tramos. Así no hace falta un hook en `jobs/worker.py`.
- **Descartadas**:
  - Renumerar la 5 de 014: rompe las bases que ya la aplicaron.
  - Completar los tramos en el worker al terminar: exige un hook nuevo y acopla `transcribe` a los proyectos de mezcla.
  - Que `prepare` espere la transcripción: bloquea la petición mientras corre el modelo.
- **Cómo revertir**: el commit de la API de mezcla (migración, `db/mix_projects.py`, `api/routes/mix.py`, `services/mix_render.py`).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_mix.py` (caché → tramos al momento; sin caché → trabajo `transcribe`; migración 6 sin BLOB).
- **Pendiente**: ninguno.
