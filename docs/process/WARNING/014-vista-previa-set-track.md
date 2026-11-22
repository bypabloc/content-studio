# 014: la vista previa no tira el editor si el documento cambia antes de que JASSUB esté lista (ciclo 8)

**Qué pasó.** `SubtitlesPreview` llamaba `renderer.current?.renderer.setTrack(ass)` en cada cambio del ASS. JASSUB asigna `renderer` cuando su worker está listo. Si el documento cambiaba antes, el `TypeError` salía dentro de un efecto de React y desmontaba el editor, con el autoguardado pendiente. Lo encontró el e2e `happy-import-edit-export`.

**Qué se decidió.** La pista se manda cuando `ready` se resuelve, sobre la instancia recién creada. Los cambios posteriores solo llegan si `renderer` ya existe. Un fallo del worker (sin WebGL) deja la vista previa vacía y no tira el editor.

**Dónde.** `client/src/features/subtitles/SubtitlesPreview.tsx`. Prueba de regresión: `tests/e2e/subtitles/happy-import-edit-export.e2e.ts`.
