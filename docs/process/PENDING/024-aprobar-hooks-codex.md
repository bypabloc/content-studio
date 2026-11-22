# 024: aprobar en Codex los hooks del proyecto

- **Qué**: abrir Codex en el checkout, correr `/hooks` y aprobar `shell_guard.py` y `computer_use_guard.py`. Después, pedirle `sky.list_apps()` y comprobar que el hook lo bloquea.
- **Por qué no se hizo**: la aprobación es interactiva y la guarda Codex en la configuración del usuario. El atajo `--dangerously-bypass-hook-trust` está bloqueado por Synapse.
- **Cuándo**: después del merge de la 024, y de nuevo cada vez que cambie un hook.
- **Quién**: usuario.
- **Qué la cierra**: `/hooks` muestra los dos como confiables y el intento de Computer Use sale bloqueado.
