# 008: `UIText` acepta `className`, y 15 usos de features/app lo necesitan

- **Qué**: `UIText` acepta `className`, que trae klinikae. Desde la T5 lo combina con `cn(base, className)` en vez de concatenarlo. Hay 15 usos en `features/` y `app/` (por ejemplo, `CompareTakes.tsx` y `NarrationResult.tsx`) que ajustan peso y tamaño con `font-medium`, `text-sm` o `text-xs`.
- **Por qué no se hizo**: la regla de UI no dice si los átomos de texto admiten `className`, y las pantallas lo usan hoy. No está probado que `cn` resuelva el conflicto con las clases `ui-typography-*`.
- **Cuándo**: después de la 009, que toca los mismos textos.
- **Quién**: agente.
- **Qué la cierra**: decidir si `UIText` conserva `className` (y cuáles usos pasan a una variante), o si solo lo tienen `UIBox`, `UIStack` y `UIGrid`. Se registra en una ficha WARNING.
