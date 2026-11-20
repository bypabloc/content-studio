# 010: el cliente de la API suma PATCH y la subida de un cuerpo crudo; borrar siempre pide la papelera

- **Contexto**: el server renombra con `PATCH /voices/profiles/{slug}` y guarda una toma con el WAV crudo en el cuerpo, sin multipart. El cliente solo tenía GET, POST, PUT y DELETE, y serializaba todo como JSON.
- **Elegida**: `request` acepta un tipo de contenido opcional: con él, el cuerpo va tal cual (`upload`); sin él, va como JSON, como antes. `patch` se agrega junto a `put`. Borrar siempre manda `confirm=true`: el server lo manda a la papelera, y el diálogo ya pidió confirmación.
- **Descartadas**: una función aparte con su propio `fetch` (duplica cabeceras y manejo de errores); mandar primero sin `confirm` y tratar el 409 `profile_not_empty` como segundo paso (dos llamadas por cada borrado).
- **Cómo revertir**: quitar `patch` y `upload` de `client.ts` y el parámetro `contentType`; `useVoices.ts` los usa.
- **Cómo comprobarla**: `client/tests/unit/src/shared/api/client.test.ts` (PATCH con JSON; subida con `audio/wav` y el cuerpo sin serializar).
- **Pendiente**: la subida de tomas se usa en el 7c (`RecordWizard`).
