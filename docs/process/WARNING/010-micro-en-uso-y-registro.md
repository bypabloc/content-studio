# 010: indicador «Micrófono en uso» y registro del micrófono, apagado por defecto

- **Contexto**: el usuario pidió (a) algo visible que diga que el micrófono está en uso, en vez de pedir permiso, y (b) un registro de los eventos del micrófono en una carpeta, que se pueda encender y apagar en Ajustes y que esté apagado por defecto.
- **Elegida, indicador**: icono `mic` en rojo con «Micrófono en uso» en el asistente de grabación, mientras el micrófono se abre, graba o corre la prueba de sala. Al subir la toma ya no se muestra: el micrófono está suelto.
- **Elegida, registro**: el ajuste `diagnostics.recording_log` (apagado por defecto). Encendido, el cliente manda cada evento a `POST /diagnostics/recording` y el server agrega una línea JSON a `logs/recording/AAAA-MM-DD.log` (`paths.LOGS`). Apagado, no se llama a la API y no se crea la carpeta.
- **Eventos que se anotan**: `mic.list` y `mic.list.error` (desde Ajustes), `record.start` y `record.start.error`, `record.stop`, `room.result` y `room.failed`.
- **Descartadas**: un registro siempre encendido (el usuario pidió apagado por defecto); guardar también el audio (no se pidió, y es dato del usuario); crear la carpeta al arrancar.
- **Límite**: el registro guarda nombres de micrófono, identificadores de dispositivo y niveles de la prueba de sala. Queda en `logs/`, que está gitignoreado.
- **Cómo revertir**: quitar `useRecordingLog` de `RecordWizard` y de `SettingsPage`, la ruta `api/routes/diagnostics.py` y su línea en `app.py`.
- **Cómo comprobarla**: `test_diagnostics.py` (3 pruebas), `recordingLog.test.tsx` (apagado no escribe, encendido escribe) y la prueba del indicador en `RecordWizard.test.tsx`. Con el micrófono real, pendiente de la prueba del usuario.
