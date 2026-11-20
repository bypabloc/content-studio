# 008: el tema de content-studio se adapta, no se reemplaza

- **Contexto**: los componentes de klinikae usan colores y sombras que content-studio no define, como `foreground-secondary`, `primary-hover` o `shadow-ui`. La tipografía y las utilidades (`ui-focus`, `ui-press`) vienen del paquete de tokens de klinikae.
- **Elegida** (D-6):
  - `client/src/styles/tokens.css` suma, en claro y en oscuro, los colores que faltan: `foreground-secondary`, `primary-hover`, `destructive-soft`, `success`, `success-soft`, `accent-foreground` y `shadow-ui` (con `-sm` y `-lg`). Salen de la paleta oklch de `index.css`: mismo tono, otra luminosidad.
  - `client/src/styles/utilities.css` copia `ui-typography-*`, `ui-focus` y `ui-press` de klinikae (`tokens/utilities.css`).
  - `client/src/index.css` importa `tailwindcss`, `tw-animate-css` y los dos archivos de `styles/`. No importa `shadcn/tailwind.css`: la spec lo pedía, pero las primitivas de shadcn no lo necesitan.
  - `client/tests/unit/src/styles/tokens.test.ts` comprueba que cada token exista en `:root` y en `.dark`, y que `foreground-secondary` tenga contraste AA (4,5:1) sobre el fondo en los dos temas. Pasa: 39 pruebas.
- **Descartadas**: reemplazar el tema por la paleta de klinikae. El usuario eligió adaptarlo.
- **Cómo revertir**: quitar las variables sumadas en `tokens.css` y los imports de `index.css`. Los componentes perderían esos colores, así que hay que revertirlos también.
- **Cómo comprobarla**: `bun run --cwd client vitest run tokens`, y la prueba axe de `tests/e2e/shell/happy-apariencia-axe.e2e.ts` (AC-8).
- **Antes de**: el merge a `dev`.
