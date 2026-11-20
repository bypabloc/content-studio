# 008: los 16 componentes de klinikae que no se copian

- **Contexto**: D-3 trae los componentes genéricos de klinikae. Hay 16 que son de otros productos (clínica, auth, web pública, encuestas, usuarios y móvil), y ninguna pantalla de content-studio los usa.
- **Elegida**: no copiarlos. Quedan fuera, con su motivo:
  - De la clínica: `UIOdontogram`, `UIBodyMap`, `UIStockBadge` y `UIScheduleGrid`.
  - De auth y la web pública: `UITurnstile`, `UIProviderButton`, `UIAuthLayout`, `UIPortalShell`, `UIPublicPageFallback`, `UIBrand` y `UIBrandLink`.
  - De encuestas: `UINps`, `UIScale` y `UIMatrix`.
  - Sin usuarios ni modo móvil: `UIUserMenu` y `UIBottomNav`.
- **Descartadas**: copiarlos por si acaso. Sería código sin uso (plan-format §0, K.I.S.S.).
- **Cómo revertir**: copiar el componente desde klinikae a `atoms/`, `molecules/` u `organisms/`, con su `index.tsx` y su test espejo.
- **Cómo comprobarla**: `bun run --cwd client vitest run inventory`. El inventario exige que las carpetas sean exactamente la lista, así que un componente extra falla.
- **Antes de**: el merge a `dev`.
