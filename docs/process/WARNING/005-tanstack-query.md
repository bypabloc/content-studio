# 005: TanStack Query para los datos del server (dependencia nueva)

- **Contexto**: la cola, el historial y la biblioteca piden los mismos datos desde varias pantallas, y SSE tiene que actualizarlos en vivo. Con `fetch` y `useEffect` en cada pantalla, cada una pediría de nuevo y las pantallas se desfasarían.
- **Elegida**: `@tanstack/react-query` 5.108.1 (versión exacta). Su caché es la que SSE actualiza con `setQueryData` (`client/src/shared/api/events.ts`), sin volver a pedir.
- **Descartadas**: `fetch` con `useEffect` (cada pantalla pide por su cuenta); SWR (la misma idea con menos herramientas para mutaciones); un store propio (más código que mantener).
- **Cómo revertir**: quitar `@tanstack/react-query` de `client/package.json`, cambiar `Providers.tsx` por un contexto con el cliente y reemplazar `setQueryData` por el store elegido en `events.ts`.
- **Cómo comprobarla**: `cd client && bun run test` (incluye `tests/unit/src/shared/api/events.test.ts`, que comprueba que la caché cambia sin pedidos).
- **Antes de**: el merge a `dev`, porque agrega una dependencia nueva que hay que aceptar.
