# 021: los capítulos de Publicar no saltan en el reproductor

- **Qué**: D-5 pide que los capítulos de «Publicar» salten al reproductor del detalle. Hoy se muestran como texto copiable (`0:00 Inicio`), pero el detalle de la Biblioteca no expone el reproductor para moverlo.
- **Por qué no se hizo**: `ItemDetail` usa `UIMedia` sin una referencia al elemento ni un control de posición. Sumarlo toca el reproductor compartido, fuera del alcance de las tareas del asistente.
- **Cuándo**: con la próxima spec de la Biblioteca o del reproductor.
- **Quién**: agente.
- **Qué la cierra**: pulsar un capítulo en Publicar mueve el video o el audio del detalle a ese segundo, con su prueba en `PublishTab.test.tsx`.
