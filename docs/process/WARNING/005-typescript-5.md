# 005: TypeScript 5.9.3 en vez de TypeScript 7 (la API de openapi-typescript)

- **Contexto**: `openapi-typescript` 7.13.0 usa la API JavaScript de TypeScript (`ts.factory`) y declara `typescript ^5.x` como peer. TypeScript 7 es el compilador nativo en Go y no la expone: `gen:api` falla con `Cannot read properties of undefined (reading 'createKeywordTypeNode')`.
- **Elegida**: `typescript` 5.9.3 (exacta), la última 5.x. Así el `tsc` del typecheck y el generador usan el mismo compilador.
- **Descartadas**: dos compiladores (TypeScript 7 para `tsc` y 5.x solo para generar), que duplica herramientas; escribir los tipos a mano desde OpenAPI, que se desfasa del server.
- **Cómo revertir**: subir `typescript` a 7.x en `client/package.json` cuando `openapi-typescript` declare soporte para su nueva API (revisar la `peerDependencies` de la versión nueva).
- **Cómo comprobarla**: `cd client && bun run gen:api && bun run typecheck`.
- **Pendiente**: ninguno; revisar al subir `openapi-typescript` (ver *Cómo revertir*).
- **Antes de**: el merge a `dev`.
