# 030: app-check registra 154 peticiones 403 a /media/peaks de las voces

- **Qué**: en `app-check run` (run `20261125-071959`, commit 33576cf) las dos pasadas de smoke pasan, con cero errores de consola, pero el reporte anota 154 respuestas `403` a `/media/peaks` de las voces de `server/data/narration/voices/`.
- **Por qué no se hizo**: no es de carpetas de entrada; la base de la prueba es temporal y esas rutas de voces no se sirven desde ella. Parece el control de rutas de `/media`, pero no está comprobado que sea lo esperado.
- **Cuándo**: después de publicar 030.
- **Quién**: agente.
- **Qué lo cierra**: confirmar que el 403 es el comportamiento esperado de `/media/peaks` fuera de las raíces de la base, o corregir la ruta que lo pide.
