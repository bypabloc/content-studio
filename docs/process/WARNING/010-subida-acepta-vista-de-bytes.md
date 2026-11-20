# 010: el cliente acepta una vista de bytes como cuerpo de la subida

- **Contexto**: con TypeScript 5.9, `Uint8Array` lleva el tipo de su buffer como parámetro; `BodyInit` no lo acepta y `tsc` falla al subir la toma WAV (`useTakes.ts`).
- **Elegida**: `upload` acepta `BodyInit | ArrayBufferView`. El cuerpo sigue pasando tal cual a `fetch`, como antes.
- **Descartadas**: un `as BodyInit` en `useTakes` (oculta el tipo justo donde se sube); cambiar `encodeWav` (toca la captura ya probada).
- **Cómo revertir**: volver a `body: BodyInit` en `client.ts` y convertir el WAV en `useTakes`.
- **Cómo comprobarla**: `cd client && bunx tsc --noEmit`.
- **Pendiente**: ninguno.
