# 005: el anuncio de la cola no se borra cuando no hay destino

- **Qué**: el anuncio de reordenar no borra el anterior cuando no hay destino (`features/queue/announce.ts`), así que el lector de pantalla sigue leyendo el último lugar. La etiqueta de la región de sonner ya la cerró la 007 (`notify.region` en los tres idiomas).
- **Por qué no se hizo**: el anuncio vacío necesita una prueba con dnd-kit.
- **Cuándo**: después de la 005.
- **Quién**: agente.
- **Qué la cierra**: un test de `announce.ts` sin destino que devuelva el anuncio vacío.
