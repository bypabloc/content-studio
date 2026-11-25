# 039: app-check muestra «Instala el motor de diarización» aunque pyannote está instalado

- **Qué**: en las capturas de `app-check` (también con `--data=real`), Transcripción, Hablantes, Subtítulos y Limpiador muestran «Instala el motor de diarización para identificar hablantes» y el interruptor apagado. La pantalla lee `pyannote.status === installed` del servidor de la app, y ese servidor corre con `CONTENT_STUDIO_HOME` en una carpeta de `app-check`, donde pyannote no está. Con `--data=real` la base dice `fresh`: el modo real no usa la carpeta de motores del usuario.
- **Cómo cerrarlo**: o bien `--data=real` usa la carpeta de motores del usuario (en `devtools/app_check/env.py`), o bien las capturas de hablantes se toman en la app instalada. Después se revisa que el aviso no aparezca con pyannote instalado.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente.
