# 012: validar las reglas actualizadas con Codex CLI

- **Qué**: comprobar las reglas `stack`, `codigo-python` y `worktrees` con una consulta general, una trampa y una consulta negativa por cada regla.
- **Por qué no se hizo**: Synapse permitió editar y sincronizar las reglas, pero bloqueó ejecutar `codex exec` en modo no interactivo porque requiere autorización manual para lanzar otro agente.
- **Cuándo**: después de que el usuario autorice esa ejecución.
- **Quién**: usuario y agente.
- **Qué la cierra**: correr las nueve consultas con Codex CLI sin web ni MCP, registrar `9/9 PASS` y eliminar esta ficha y su fila.
