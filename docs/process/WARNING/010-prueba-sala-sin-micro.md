# 010: si el micrófono no abre, la prueba de sala avisa y no deja el temporizador corriendo

- **Contexto**: `recorder.start()` puede rechazar (permiso denegado). Sin manejar, la promesa dejaba un temporizador que después habría dado un nivel de `-Infinity` dBFS en pantalla.
- **Elegida**: el rechazo cancela el temporizador, marca `failed` y el asistente muestra el aviso de micrófono.
- **Descartadas**: ignorar el rechazo (una promesa sin manejar y un dato falso en pantalla).
- **Cómo revertir**: quitar el `.catch` de `useRoomTest.run`.
- **Cómo comprobarla**: `useRoomTest.test.ts`, «si el micrófono no abre, avisa y el temporizador no sigue». Este test se escribió después del GREEN, al revisarlo; pasa con el código actual.
- **Pendiente**: ninguno.
