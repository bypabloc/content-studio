# 005: `worktree` no limpia enlaces rotos y `close` falla si la carpeta se borró a mano

- **Qué**: `remove_links` no quita un enlace roto, porque el glob de pathlib solo devuelve rutas que existen. Y `close` o `prepare` terminan con traceback si la carpeta de un worktree se borró a mano y Git sigue registrándolo.
- **Por qué no se hizo**: el caso es raro y no pierde datos (el enlace roto no apunta a nada); el arreglo toca el glob de todos los enlaces.
- **Cuándo**: después de la 005, o antes si pasa en una corrida real.
- **Quién**: agente.
- **Qué la cierra**: un test con un enlace roto y otro con la carpeta borrada, que `close` y `prepare` resuelvan con un mensaje claro.
