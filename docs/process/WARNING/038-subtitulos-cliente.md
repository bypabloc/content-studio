# 038: decisiones del cliente de subtítulos con hablantes (fase 2)

- **Contexto**: la vista previa (ASS del cliente) tiene que pintar igual que el ASS del server, que pone `\1c` con un reemplazo de la primera línea `,Default,,0,0,0,,` (`server/src/content_studio/subtitles/ass.py`).
- **Elegida**: `tint` en `client/src/features/subtitles/ass.ts` con el mismo reemplazo, en los modos `classic` y `social`. `karaoke` no cambia.
- **Descartadas**: `\c` por palabra (otra salida que el server; la vista previa no sería la que se exporta).
- **Cómo comprobarla**: `bun run --cwd client test -- subtitles` (`ass.test.ts`).

- **Contexto**: Subtítulos y Transcripción guardan el modelo (`select.whisper.model`) y el idioma (`select.transcription.language`) en los mismos ajustes.
- **Elegida**: Subtítulos los reutiliza con `UIWhisperModelSelect` y `useRecommendedValue`, así el usuario elige una vez. La lista de siete códigos de idioma se repite en `SubtitlesPage.tsx` y `TranscriptionForm.tsx` (ver `PENDING/038-idiomas-duplicados.md`).
- **Descartadas**: ajustes propios de Subtítulos (dos elecciones que pueden divergir).
- **Cómo comprobarla**: `SubtitlesPage.test.tsx` («queues a file with its model…») y `tests/e2e/subtitles/happy-speakers.e2e.ts`.

- **Contexto**: `features/` no puede importar `UIBox` (lint, D-4) y el chip del cue necesita un punto de color; `ui-structure` rechaza un `span` nativo.
- **Elegida**: `UISpeakerChip` en `shared/components/molecules/UISpeakerLegend`, que usa `CueList`.
- **Descartadas**: `span` nativo (lo rechaza `ui-structure`); `UIBox` dentro de `features/` (lo rechaza el lint).
- **Cómo comprobarla**: `python -m devtools test-runner --type=client-lint,ui-structure`.

- **Contexto**: las pruebas que ya esperaban el cuerpo exacto de `POST /jobs` (origen y ruta) no contaban `model` ni `language`, que ahora van en cada envío de Subtítulos.
- **Elegida**: `expect.objectContaining` en esas aserciones (`SubtitlesPage.test.tsx`, y `happy-from-file`, `happy-import-edit-export` y `neg-import-invalid` en e2e). Siguen comprobando el origen y la ruta.
- **Descartadas**: no mandar `model` ni `language` cuando el origen no transcribe: el contrato del trabajo sería distinto según el origen.

- **Contexto**: exportar no guardaba el borrador. Si se renombraba un hablante y se exportaba antes de que el autoguardado (1 s) lo enviara, el archivo salía con el nombre anterior.
- **Elegida**: la exportación guarda el borrador antes de pedir el archivo, como ya hacían quemar y traducir. Prueba: `SubtitlesEditor.test.tsx` («guarda el borrador antes de exportar»).
- **Descartadas**: dejarlo como pendiente (el AC-4 exige que el nombre nuevo salga en el archivo).
