# 008: `cn` se toma del paquete `cn` 0.5.0 de shadcn, no de un `clsx` + `tailwind-merge` propio

- **Contexto**: las primitivas de shadcn y los componentes de klinikae importan `cn` desde `"cn"`. Hay que fijar esa dependencia con la versión de klinikae, y revisar su licencia y su código antes.
- **Elegida**: `cn@0.5.0` (exacta), como en klinikae. Licencia MIT, repositorio `shadcn-ui/cn` (el de la organización de shadcn), y es un reemplazo directo de `clsx` + `tailwind-merge` con un solo import.
- **Descartadas**:
  - `client/src/shared/lib/cn.ts` con `clsx` + `tailwind-merge` y un alias: funcionaría, pero es una dependencia más y un alias que mantener, sin ventaja para lo que hace el código copiado.
  - Reescribir cada import: muchos archivos copiados cambiarían sin necesidad.
- **Cómo revertir**: sustituir `cn` por `clsx` + `tailwind-merge` en `client/src/shared/lib/cn.ts` y apuntar el alias `cn` de `vite.config.ts` y `tsconfig` a ese archivo; los imports copiados no cambian.
- **Cómo comprobarla**: `bun run --cwd client test -- smoke` importa las 27 primitivas, todas usan `cn`; `client-typecheck` pasa.
- **Antes de**: el merge a `dev` (se revisó en esta spec; no bloquea `main`).
