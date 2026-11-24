# 023: detalles menores vistos en el recorrido

- **Qué**: (1) «Sugerir palabras clave» devolvió «timbre,» con la coma como palabra. (2) Al cambiar la fuente de un proyecto de subtítulos, `subtitles.burn` guarda en `params.source` la ruta vieja de la columna `source_path`, aunque quema la fuente nueva del documento (el audio medido lo confirma). (3) El chequeo de una toma importada de una referencia ya masterizada da «retake» por bordes sin silencio: es correcto para una grabación, pero no distingue una referencia lista. (4) `app-check` deja la bienvenida marcada como vista, así que `--scenario=installed` no la captura.
- **Por qué no se hizo**: ninguno bloquea; cada uno es de una spec cerrada.
- **Cuándo**: después del lote.
- **Quién**: agente.
- **Qué la cierra**: (1) recortar la puntuación de `word` en `subtitles_keywords`; (2) actualizar `source_path` al guardar el documento; (3) un aviso distinto para referencias masterizadas; (4) un escenario de bienvenida con la base sin `welcome.done`.
