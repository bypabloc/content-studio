# 005: avisos de sonner y anuncio de la cola en inglés o sin borrar

- **Qué**: sonner pone en inglés la etiqueta de su región de avisos (lector de pantalla), y el anuncio de reordenar no borra el anterior cuando no hay destino (`features/queue/announce.ts`), así que el lector sigue leyendo el último lugar.
- **Por qué no se hizo**: la etiqueta de la región necesita revisar la API de sonner de la versión fijada; el anuncio vacío necesita una prueba con dnd-kit.
- **Cuándo**: después de la 005.
- **Quién**: agente.
- **Qué la cierra**: la región con su texto de `es.json` y un test de `announce.ts` sin destino que devuelva el anuncio vacío.
