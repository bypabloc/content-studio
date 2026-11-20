# 011: generar las 126 muestras de 10 s del buscador de Música

- **Qué**: correr `studio music samples` sin filtro para que cada preset tenga su `server/data/music/samples/<preset>.wav`. Sin ellas, el ▶ del buscador no suena.
- **Por qué no se hizo**: es una corrida larga en GPU (una muestra detrás de otra, con el candado) y no bloquea el código ni el merge. Solo `lofi-chill` se generó en la verificación del grupo 4.
- **Cuándo**: después del merge a `dev`, antes de usar el buscador en la app.
- **Quién**: agente, con el candado de la GPU (`studio` lo toma solo), o usuario.
- **Qué la cierra**: `ls server/data/music/samples/*.wav | wc -l` da 126, y `GET /music/styles` marca `has_sample: true` en todos.
