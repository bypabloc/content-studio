# 008: cómo traer las mejoras de klinikae sin paquete compartido

- **Qué**: los componentes se copiaron de klinikae a mano. Una mejora que se haga allá no llega a content-studio hasta que alguien la copie.
- **Por qué no se hizo**: son tres caminos con costos distintos, y los elige el usuario: (a) seguir copiando a mano, (b) un script que compare cada componente con klinikae y muestre el diff, o (c) un paquete compartido entre los dos repos.
- **Cuándo**: cuando haya que traer un cambio de klinikae. No bloquea nada.
- **Quién**: usuario (elige el camino).
- **Qué la cierra**: la elección entre (a), (b) y (c), registrada en una ficha WARNING.
