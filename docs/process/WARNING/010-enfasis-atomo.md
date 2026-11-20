# 010: el énfasis del guion es el átomo `UIEmphasis`, no un `strong` en la pantalla

- **Contexto**: la etapa `ui-structure` no deja etiquetas nativas como `strong` fuera de los átomos. El teleprompter necesita la negrita de la notación (`**palabra**`).
- **Elegida**: un átomo `UIEmphasis` (negrita sin cambiar el tamaño ni el color del texto que lo rodea), con su prueba en el espejo y su fila en el inventario de átomos (`inventory.test.ts`).
- **Descartadas**: quitar la negrita (la notación la explica, y perdería el énfasis del guion); una molécula (no compone átomos).
- **Cómo revertir**: mostrar `style.marked` como texto plano en `Teleprompter.tsx`, y quitar `UIEmphasis` del inventario.
- **Cómo comprobarla**: `cd client && bunx vitest run tests/unit/src/shared/components/atoms/UIEmphasis tests/unit/src/shared/components/inventory.test.ts`, y la etapa `ui-structure` del gate.
- **Pendiente**: ninguno.
