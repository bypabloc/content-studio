# Revisiones pendientes que no bloquean

Lo que se revisa **después** y no impide pasar a `main`: una observación de la verificación, una mejora que quedó fuera de alcance, una escucha comparada que el usuario hará con calma. Cada ficha dice cuándo toca, quién la hace y qué la cierra, y se borra al cerrarla, con su fila. Lo que sí bloquea va en [`../WARNING/`](../WARNING/README.md).

Nombre: `<spec>-<tema>.md`. Formato:

```markdown
# <spec>: <qué revisar en una línea>

- **Qué**: la observación o el pendiente.
- **Por qué no se hizo**: fuera de alcance, falta un dato, decisión del usuario.
- **Cuándo**: antes o después de publicar; con qué spec o evento.
- **Quién**: agente o usuario.
- **Qué la cierra**: comando, prueba o decisión.
```

| Ficha | Qué | Cuándo | Quién |
| :--- | :--- | :--- | :--- |
| [lufs-de-la-mezcla](lufs-de-la-mezcla.md) | Las mezclas con picos quedan en -14,7 LUFS (AC-3 pide -14 ± 0,5): iterar un limitador, aceptar ±1,5 LU o dejarlo | Al escuchar una mezcla | Usuario |
| [hooks-en-codex](hooks-en-codex.md) | Aprobar en `/hooks` de Codex los guards del proyecto y comprobar que bloquean (también en Antigravity) | Al usar Codex | Usuario |
| [limpieza-carpetas-huerfanas](limpieza-carpetas-huerfanas.md) | Más de 150 carpetas huérfanas en `content-studio-worktrees/` que Synapse no deja borrar | Cuando quieras | Usuario |
