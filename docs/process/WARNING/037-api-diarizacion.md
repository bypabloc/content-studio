# 037: decisiones de la API de diarización y del proyecto del Editor (fase 1)

- **Contexto**: la fase 1 agrega `GET /diarizations/{id}` y `POST /editor/projects/from-diarization`. `api/routes/editor.py` tiene 278 líneas (el límite es 300), y el marcador del esquema del Editor no es el del borrador de la spec.
- **Elegida**:
  - La ruta `POST /editor/projects/from-diarization` vive en `api/routes/diarizations.py`, no en `editor.py`: sumarla lo pasaría del límite. La URL no cambia.
  - Un marcador es `{id, t, label, color}`, como lo define el esquema vigente; el borrador decía `time`. El esquema manda, como dice la propia spec.
  - El clip de audio va en la pista `t1` de `new_doc`, con id `c1`, `gain_db` 0 y `speed` 1, y pasa `project.validate`.
  - El proyecto se llama como el archivo de origen (sin prefijo): el texto visible no pasa por el validador de ortografía.
  - Un trabajo sin `turns.json` responde 409 `no_diarization`; el código nuevo tiene texto en los tres idiomas.
  - `split` es null si `speakers/` no tiene WAV: la sección ofrece «Un audio por hablante».
- **Descartadas**: la ruta en `editor.py` (pasaría de 300 líneas); el marcador con `time` (el Editor no lo lee).
- **Cómo revertir**: quitar el router de `app.py` y borrar los dos módulos y la clave `error.no_diarization`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_diarizations.py server/tests/unit/src/content_studio/editor/test_from_diarization.py`.
