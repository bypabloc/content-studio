# 019: la pista guarda el ID del proyecto de subtítulos

- **Contexto**: el esquema v3 ya tiene `subtitles_project` como string y los documentos de la 014 viven en SQLite y JSON.
- **Elegida**: guardar el ID decimal como string, resolverlo en el server al renderizar y reutilizar el documento ASS de la 014. Para crear uno nuevo, renderizar la mezcla a WAV, encolar `transcribe` y registrar sus palabras como proyecto 014.
- **Descartadas**: guardar la ruta del JSON en el proyecto del Editor (acopla el documento a una ruta local); transcribir dentro del render (evita la cola y el candado de GPU); copiar cues al proyecto del Editor (duplica el documento editable).
- **Cómo revertir**: revertir el commit `feat: pista de subtítulos en el editor` y quitar esta ficha y su fila.
- **Cómo comprobarla**: `pytest server/tests/unit/src/content_studio/editor/test_render_subtitles.py server/tests/unit/src/content_studio/api/routes/test_subtitles.py` y `bun run --cwd client vitest run tests/unit/src/features/editor/SubtitleTrack.test.tsx tests/unit/src/features/editor/SubtitleTracksPanel.test.tsx`.
- **Pendiente**: ninguna.
