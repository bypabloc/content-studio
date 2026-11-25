# 039: referencia de los clips de DER construida por montaje

- **Contexto**: el AC-3 pide clips propios con una referencia anotada a mano. Anotar a mano un clip de 72 s, dos veces, es trabajo del usuario y no se puede hacer aquí.
- **Elegida**: un diálogo montado con muestras de voz de `server/data/narration/voices` (`andrea`, `colombia-m`, `alba-mackenna`) y pausas de 0,8 s. La referencia son los instantes de cada montaje (`out/spec-039/dialogo-*/referencia.json`), exactos por construcción.
- **Descartadas**: esperar la anotación del usuario (bloquea la 039); grabar una conversación nueva (no hay quien la grabe aquí).
- **Cómo revertir**: anotar a mano dos clips reales y volver a correr el DER con ellos. Los números de `10-pruebas-en-gpu.md` se reemplazan.
- **Cómo comprobarla**: `referencia.json` de cada montaje y el DER de `10-pruebas-en-gpu.md`.
