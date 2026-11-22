# 014: proyectos y migración 5

**Qué se decidió (grupo de la API y la base, ciclo 3).** La spec dice «la migración 4» y «el POST crea el proyecto»; al ejecutarla cambian dos cosas:

- **Migración 5, no 4.** La 013 ya ocupó la 4 (`transcripts`, `user_version` 4). `subtitle_projects` es la 5 (`PRAGMA user_version` = 5). `db/test_schema.py` se actualiza a 5.
- **El proyecto se registra al terminar el trabajo, no en el POST.** El `output_dir` lo asigna el worker al arrancar el trabajo (`jobs/worker.py`, `_output_dir`), así que el POST no conoce la ruta del `subtitles.json`. `_chain` inserta la fila cuando `subtitles.create` termina con su documento.
- **POST /subtitles encola** `subtitles.create` y responde 201 con el `Job`, igual que `POST /clean/{id}/render`. El proyecto aparece en `GET /subtitles` al terminar.
- **DELETE no borra archivos.** Quita la fila y mueve la carpeta del proyecto a `subtitles/.trash/` (dentro de `outputs_dir()`).
- **Nombre del proyecto**: el nombre del video de `source.path` del documento (sin extensión).

**Dónde.** `db/schema.py` (migración 5), `db/subtitle_projects.py`, `jobs/worker.py` (`_chain`), `api/routes/subtitles.py`, catálogos `messages/{es,en,pt}.json` (`error.subtitle_project_not_found`).

**Por qué.** Seguir la spec al pie daría dos migraciones con el número 4 o una ruta inexistente en el POST. La tabla guarda solo nombre y rutas (D-1), y el documento queda en disco.
