# 005: la notificación de Windows y el sonido del aviso, a comprobar a mano

- **Qué**: AC-5 pide que, con la ventana minimizada o sin foco, al terminar un trabajo salga la notificación de Windows y suene el aviso corto. En la verificación real (T9) se comprobó el toast dentro de la app («Trabajo terminado», con «Abrir carpeta»), el progreso de la fila y el cierre limpio del server. La notificación del sistema y el sonido no se comprobaron, y el avance intermedio de un trabajo de 15 s no se capturó (el trabajo pasó de 0 % a terminado entre sondeos).
- **Por qué no se hizo**: la notificación sale del centro de acciones de Windows y el sonido por el altavoz; no se leen por CDP ni por captura de la ventana.
- **Cuándo**: al primer uso real de la app, o antes del instalador (022).
- **Quién**: el usuario. Pasos: encolar un trabajo de música, minimizar la ventana, esperar el final. Después, mirar el centro de notificaciones y escuchar el sonido. Para el avance intermedio, un trabajo de 60 s o más.
- **Qué la cierra**: la notificación aparece con la ventana minimizada y el sonido suena (o se abre una ficha WARNING si no ocurre).
