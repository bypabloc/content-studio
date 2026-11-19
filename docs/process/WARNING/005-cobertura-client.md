# 005: cobertura del client: 80 % por archivo, sin shadcn ni `main.tsx`

- **Contexto**: el gate `client-unit` tiene que exigir cobertura por archivo (D-9), pero el proyecto aún no copia shadcn (`src/components/ui/` no existe; la desviación de D-1 está en `docs/process/WARNING/005-desvios-de-diseno.md`), así que la exclusión queda para cuando se copie, como código ajeno, y `main.tsx` solo monta la app y bloquea el menú contextual: testearlos con jsdom no aporta y no cambia lo que el usuario ve.
- **Elegida**: `coverage.include` = `src/**`; `exclude` = `src/components/ui/**`, `src/main.tsx` y los `.d.ts` (el `schema.d.ts` lo genera `openapi-typescript`). Umbral de 80 % en líneas, funciones, ramas y sentencias, con `perFile: true` (`client/vite.config.ts`).
- **Descartadas**: cobertura global (un archivo sin tests pasa si los demás sobran); incluir shadcn (exige tests de componentes de terceros); no medir nada en el client.
- **Cómo revertir**: quitar `perFile` o los `exclude` en `client/vite.config.ts`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=client-unit` (falla si un archivo de `src/` baja de 80 %).
- **Pendiente**: ninguno.
- **Antes de**: el merge a `dev`.
