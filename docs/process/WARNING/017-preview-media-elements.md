# 017: la vista previa transmite cada clip por un elemento multimedia

- **Contexto**: decodificar por completo cada archivo con `decodeAudioData` consume memoria proporcional a su duración y tamaño.
- **Elegida**: un `HTMLAudioElement` por clip activo conectado a WebAudio mediante `MediaElementSourceNode` y `GainNode`; `AudioContext.currentTime` marca la posición y corrige deriva mayor de 50 ms.
- **Descartadas**:
  - Decodificar todo el archivo: duplica en memoria el audio comprimido y la forma de onda PCM.
  - Reproducir un solo elemento compartido: no permite superponer pistas independientes.
- **Cómo revertir**: cambiar el scheduler en `client/src/features/editor/playback/` y volver a medir memoria, solapamientos y deriva.
- **Cómo comprobarla**: `client/tests/unit/src/features/editor/playback/` cubre selección de clips activos, rampas, corrección de deriva y fin del transporte.
- **Pendiente**: ninguna decisión pendiente; la escucha prolongada queda a criterio del usuario.
