# 010: en el ciclo 7b la navegación trae solo «Mis voces»; «Catálogo» entra en el 7d con su pantalla

- **Contexto**: el plan de la spec pone «Mis voces» y «Catálogo» en el grupo Voces (D-6). Si las dos entradas entran en el mismo commit, «Catálogo» apuntaría a una pantalla que todavía no existe.
- **Elegida**: el 7b agrega solo la entrada «Mis voces» en `client/src/app/nav.ts` y su pantalla. La entrada «Catálogo» y `CatalogPage` entran juntas en el 7d, en el mismo commit. El resultado final de la spec no cambia.
- **Descartadas**: una entrada «Catálogo» con un texto de «pronto»: sería una pantalla a medias que el usuario vería.
- **Cómo revertir**: no hay contrato que revertir; la entrada es una línea de `nav.ts`.
- **Cómo comprobarla**: `client/tests/unit/src/app/nav.test.ts` (grupo Voces). En el 7d, `CatalogPage.test.tsx`.
- **Pendiente**: el 7d (catálogo, ★ favorita, construir y muestras).
