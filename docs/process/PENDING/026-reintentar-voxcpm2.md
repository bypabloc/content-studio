# 026: voxcpm2 en Python 3.15 cuando pyahocorasick tenga rueda cp315

- **Qué**: probar voxcpm2 en 3.15 con torch 2.14.1+cu130 y subir la receta solo si instala y genera.
- **Por qué no se hizo**: pyahocorasick 2.3.1 no tiene rueda cp315 para Windows; compilarla desde fuente no es reproducible.
- **Cuándo**: después de publicar, o al salir una pyahocorasick con `cp315-win_amd64`.
- **Quién**: agente.
- **Qué la cierra**: la rueda en PyPI y una instalación y salida corta correctas en 3.15.
