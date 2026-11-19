# 005: cobertura del client: 80 % por archivo, sin shadcn ni `main.tsx`

- **Contexto**: el gate `client-unit` tiene que exigir cobertura por archivo (D-9), pero los componentes de `src/components/ui/` son copia de shadcn (se mantienen como código ajeno) y `main.tsx` solo monta la app y bloquea el menú contextual: testearlos con jsdom no aporta y no cambia lo que el usuario ve.
- **Elegida**: `coverage.include` = `src/**`; `exclude` = `src/components/ui/**`, `src/main.tsx` y los `.d.ts` (el `schema.d.ts` lo genera `openapi-typescript`). Umbral de 80 % en líneas, funciones, ramas y sentencias, con `perFile: true` (`client/vite.config.ts`).
- **Descartadas**: cobertura global (un archivo sin tests pasa si los demás sobran); incluir shadcn (exige tests de componentes de terceros); no medir nada en el client.
- **Cómo revertir**: quitar `perFile` o los `exclude` en `client/vite.config.ts`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=client-unit` (falla si un archivo de `src/` baja de 80 %).
- **Pendiente**: ninguno.
- **Antes de**: el merge a `dev`.
