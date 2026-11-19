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
| [001-duracion-de-audio](001-duracion-de-audio.md) | La duración de música y narración no coincide con la pedida (igual en `dev`) | Antes de publicar el lote | Usuario y agente |
| [002-cspell-excepciones-temporales](002-cspell-excepciones-temporales.md) | Exclusiones de cspell que quedan a propósito: `cli/` (004), `grabar/` (007) y textos en español de D-1 | La 004 y la 007 | Agente |
| [002-nombres-en-disco](002-nombres-en-disco.md) | `aprobacion.json` de las voces construidas sigue en español | Antes de publicar, o en la 004 | Usuario y agente |
| [003-bajar-baselines](003-bajar-baselines.md) | Vaciar los baselines de tamaño, espejo y cobertura, y los overrides de mypy, a medida que se tocan los archivos | En cada spec que toque un módulo de la lista; `cli/` (004) y `grabar/` (007) | Agente |
| [shell-guard-codex-antigravity](shell-guard-codex-antigravity.md) | El bloqueo de `sleep` y `wsl` no se probó en Codex ni en Antigravity | Al usar esas herramientas | Usuario |
