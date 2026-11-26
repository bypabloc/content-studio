# 033: El server que arranca studio mcp muere al cerrar un cliente MCP hecho con el SDK de Python

- **Qué**: el cliente stdio del SDK `mcp` de Python mete el proceso en un Job Object con `KILL_ON_JOB_CLOSE` y sin `BREAKAWAY_OK`. El server compartido que `studio mcp` lanza queda dentro y muere al cerrar el cliente: en la corrida real, una música en curso quedó `interrupted`. El fix de la 033 (`runtime/instance.py`) pide `CREATE_BREAKAWAY_FROM_JOB` y sirve con los jobs que lo permiten. Con el del SDK no puede, y el server arranca igual dentro del job.
- **Por qué no se hizo**: salir de un job que no permite breakaway exige lanzar el server desde otro proceso (WMI `Win32_Process.Create`, el Programador de tareas o la ventana de Tauri). Es un cambio de arranque más grande que el alcance de la 033. Claude Code (Node) no usa Job Objects, así que el caso afecta a clientes en Python.
- **Cuándo**: después de publicar, o antes si un cliente real lo sufre.
- **Quién**: agente.
- **Qué la cierra**: un cliente del SDK de Python que cierra sin cortar un trabajo en curso, y `studio api status` vivo después.
