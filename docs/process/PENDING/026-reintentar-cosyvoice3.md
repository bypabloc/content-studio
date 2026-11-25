# 026: cosyvoice3 en Python 3.12 o más, cuando sus pines tengan rueda

- **Qué**: probar cosyvoice3 en 3.12 con pyworld y grpcio con rueda `cp312`, o con sus pines subidos; comprobar que `onnxruntime` 1.23.2 (en lugar del 1.18.0 del upstream en Windows) genera el mismo audio, con una escucha.
- **Por qué no se hizo**: `pyworld` 0.3.4 y `grpcio` 1.57.0 no tienen rueda `cp312` para Windows; el upstream documenta 3.10.
- **Cuándo**: después de publicar.
- **Quién**: agente (versión) y usuario (escucha).
- **Qué la cierra**: instalación y salida corta en la versión más alta que quede, y la escucha del usuario sobre `onnxruntime` 1.23.2.
