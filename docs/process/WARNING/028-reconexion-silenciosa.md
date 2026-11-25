# 028: la reconexión es silenciosa, sin texto «Reactivando el servidor…»

- **Contexto**: `02-diseno.md` §5 lista la clave `server.waking`, pero AC-8 solo pide reintentar una vez. El reintento vive en el cliente de la API (`shared/api/client.ts`), que no tiene dónde mostrar un estado sin una capa nueva.
- **Elegida**: un reintento con `get_connection` ante un fallo de red. Al cambiar la conexión, `ApiProvider` vuelve a abrir el SSE (su efecto depende de la conexión), así que `events.ts` no cambia. La clave `server.waking` no se agrega: el test de i18n falla si una clave no se usa.
- **Descartadas**: un indicador global de «reactivando» (una pantalla nueva fuera de la spec); reintentar en bucle (AC-8 pide una sola vez).
- **Cómo revertir**: agregar `server.waking` a los tres catálogos y mostrarlo en `Connected` (`app/App.tsx`) mientras `reconnect` está en curso.
- **Cómo comprobarla**: `bun run --cwd client test` (`client.test.ts`: reintento, y un 500 que no reintenta). En la verificación final, el e2e `happy-server-wakes`.
