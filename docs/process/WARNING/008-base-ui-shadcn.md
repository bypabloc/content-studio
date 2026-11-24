# 008: la base de componentes es `@base-ui/react` con shadcn, con las versiones exactas de klinikae

- **Contexto**: klinikae ya tiene 64 componentes genéricos probados sobre `@base-ui/react` y las primitivas de shadcn v4. Content-studio no tiene ninguna base de controles: sus controles son HTML con clases.
- **Elegida**: `@base-ui/react@1.9.0`, `class-variance-authority@0.7.1`, `lucide-react@1.58.0`, `recharts@3.10.1`, `cn@0.5.0` como dependencias, y `shadcn@4.22.0` y los testing-library de klinikae como desarrollo. Las 27 primitivas se copian a `client/src/shared/components/shadcn/` sin cambios de lógica; solo se quita `"use client"`, se cambia `next-themes` por el `useTheme` de la app y se corrige un import relativo.
- **Descartadas**:
  - Radix: otra base; los componentes de klinikae no se podrían copiar tal cual.
  - HTML con Tailwind propio: habría que reescribir la accesibilidad de `Dialog`, `Popover` y `Combobox`.
  - Paquete compartido con klinikae: acopla los dos repos; ver `PENDING/008-sincronizar-con-klinikae`.
- **Cómo revertir**: quitar las dependencias y las copias de `shared/components/shadcn/`; los componentes de atoms y moléculas de la spec dependen de ellas.
- **Cómo comprobarla**: `bun run --cwd client test -- smoke` (27 primitivas se importan) y `python -m devtools test-runner --type=client-typecheck`.
- **Antes de**: el merge a `dev`. Con `node_modules` hoisted (`bun install --linker hoisted`), react-dom y react deben resolver a la misma copia; si no, aparece «Invalid hook call» en las pruebas.
