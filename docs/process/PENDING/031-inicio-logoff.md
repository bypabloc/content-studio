# 031: que el server arranque al iniciar sesión

- **Qué**: AC-8 pide que el server arranque con la sesión. La escritura y el borrado del valor `Run` están verificados en la app instalada, pero no se cerró ni abrió sesión en esta verificación.
- **Cómo cerrarlo**: con la app instalada, activar el interruptor, cerrar sesión de Windows, volver a entrar y ejecutar `uv run studio api status` (debe decir `alive`). Después apagar el interruptor.
- **Cuándo**: antes de publicar 031.
