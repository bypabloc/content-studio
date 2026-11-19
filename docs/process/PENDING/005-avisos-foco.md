# 005: el cableado de los avisos (sin foco y con ajuste) no tiene prueba

- **Qué**: `ApiProvider` (`shared/api/context.tsx`) decide si un trabajo terminado suena y notifica, según el foco de la ventana y los ajustes `notify.*`. La regla de cada aviso se prueba aparte, pero ninguna prueba cubre el cableado que la dispara con la ventana sin foco.
- **Por qué no se hizo**: falta simular `document.hasFocus()` y el ajuste guardado en el mismo test; no bloquea el AC-5 porque la lógica sí tiene pruebas.
- **Cuándo**: después de la 005.
- **Quién**: agente.
- **Qué la cierra**: un test de `ApiProvider` con `hasFocus` en falso y `notify.sound` activo, que compruebe la llamada a `announceFinished`.
