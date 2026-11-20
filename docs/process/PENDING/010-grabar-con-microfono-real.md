# 010: la grabación con un micrófono real no se ha probado en la app

- **Qué**: el permiso del micrófono, el nivel del medidor con la voz real, la prueba de sala y una toma a 48 kHz se comprueban con la app y un micrófono de verdad. Los tests usan un micrófono simulado. Desde el cambio de micrófono: que la app entre sin diálogo, que el micrófono elegido en Ajustes sea el que graba, y que el indicador «Micrófono en uso» aparezca mientras graba. Con el registro encendido, `logs/recording/` debe tener las líneas de esa prueba.
- **Por qué no se hizo**: el entorno de los tests no tiene micrófono; hace falta una persona hablando.
- **Cuándo**: antes de publicar la 010 (corrida real de la T9).
- **Quién**: usuario.
- **Qué la cierra**: una toma grabada en la app con su chequeo en verde, y la prueba de sala en una sala real.
