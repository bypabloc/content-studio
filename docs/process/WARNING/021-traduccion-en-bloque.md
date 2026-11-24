# 021: la traducción se acepta como pista entera

- **Contexto**: D-5 pide aceptar o descartar por cue y en bloque. En «Corregir» y «Palabras clave» se elige cue por cue. Una traducción es una pista nueva en `tracks[<idioma>]`: descartar un cue la dejaría con huecos.
- **Elegida**: la traducción se revisa cue por cue (con las marcas «Demasiado largo» y «Sin traducir») y se acepta como pista entera. Un cue se corrige después en el editor. Corregir y Palabras clave sí se aplican por cue (`accepted` en `POST /llm/subtitles/{id}/apply`).
- **Descartadas**: dejar el texto original en los cues descartados (mezcla idiomas en la pista); una pista con huecos (rompe la exportación por id).
- **Cómo revertir**: en `subtitles_translate.apply`, filtrar `result['cues']` por los `accepted`, y en `AssistantTools.tsx`, pasar `selectable` a la traducción.
- **Cómo comprobarla**: `client/tests/unit/src/features/subtitles/AssistantTools.test.tsx` («la pista se acepta entera»).
- **Pendiente**: ninguna.
