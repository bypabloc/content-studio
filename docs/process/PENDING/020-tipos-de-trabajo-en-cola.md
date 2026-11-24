# 020: la cola muestra los tipos de trabajo sin traducir

- **Qué**: `kindLabel` de `client/src/features/queue/JobRow.tsx` solo traduce `music` y `narration`; los demás tipos (`media.*`, `mix.render`, `editor.*`, `engine.*`, `library.scan`) se ven tal cual. Lo mostró la captura `library-light.png` del app-check de la 020 (`library.scan` al 0 %).
- **Por qué no se hizo**: viene de las specs anteriores y está fuera del alcance de la 020; pide una clave `queue.kind.<tipo>` por tipo en los tres catálogos.
- **Cuándo**: en la 023 (verificación integral) o en una spec de pulido de la cola.
- **Quién**: agente.
- **Qué la cierra**: cada clave de `SERVICES` tiene su `queue.kind.*` en `es`, `en` y `pt`, y una prueba de `JobRow` recorre todos los tipos.
