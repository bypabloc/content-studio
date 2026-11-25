# 038: decisiones del Editor y del Limpiador con hablantes (fase 3)

- **Contexto**: el panel de subtítulos del Editor consulta `/engines` con `useEffect`, como ya consulta sus proyectos; sus pruebas no montan `QueryClientProvider`.
- **Elegida**: el mismo patrón (`useEffect` y `api.get`) para `/engines`.
- **Descartadas**: `useQuery` (obliga a envolver las pruebas existentes del panel).
- **Cómo comprobarla**: `bun run --cwd client test -- SubtitleTracksPanel`.

- **Contexto**: el carril de subtítulos es de solo lectura en esta fase: un bloque por cue, sin acción al pulsarlo.
- **Elegida**: un `UIStack` con `role="group"` y su nombre (el texto del cue) en lugar de `UIClip`, que es un botón.
- **Descartadas**: `UIClip` (un botón sin acción).
- **Cómo comprobarla**: `client/tests/unit/src/features/editor/timeline/SubtitleLane.test.tsx`.

- **Contexto**: `cuts.json` de los análisis sin hablantes tiene que seguir igual (la prueba de parámetros lo fija).
- **Elegida**: `params.diarize` y `diarization` solo cuando está encendido «Identificar hablantes».
- **Descartadas**: `diarize: false` siempre (cambia el documento de todos los análisis).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/clean/test_analyze_main.py`.

- **Contexto**: el Limpiador diariza el archivo original (D-5). Diarizar el archivo limpio daría otra numeración de hablantes.
- **Elegida**: `diarize_file` sobre el original, con su caché por archivo; «Subtitular» no vuelve a diarizar.
- **Descartadas**: diarizar el archivo limpio.

- **Contexto**: los turnos son del audio original y los cortes quitan palabras. Asignar hablantes sobre el tiempo limpio no coincide con los turnos.
- **Elegida**: asignar hablantes sobre las palabras originales (`_cleaner_words`) y luego `clean_words`, que remapea conservando `speaker`.
- **Cómo comprobarla**: `test_ac8_cleaner_keeps_the_speakers_on_the_clean_timeline` en `test_create_main.py`.

- **Contexto**: la revisión carga sus palabras de la transcripción (`/files`), y los hablantes viven en el análisis.
- **Elegida**: `GET /clean/{id}` agrega `words` y `speakers` solo cuando hay diarización; el cliente usa `words` si llegan y, si no, la transcripción como antes.
- **Descartadas**: un segundo endpoint para las palabras con hablante.
- **Cómo comprobarla**: `test_ac8_revision_con_hablantes` y el e2e `cleaner/happy-speakers.e2e.ts`.
