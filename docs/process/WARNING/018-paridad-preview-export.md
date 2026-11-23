# 018: paridad del compositor con el render

- **Contexto**: AC-5 compara cinco instantes del compositor WebGL con `GET /editor/projects/frame`; la prueba necesita el canvas real del visor, que se implementa en T6.
- **Elegida**: ejecutar `editor/parity-preview-export.e2e.ts` en T6, antes de cerrar T7, y exigir SSIM >= 0,95 en cada instante. El compositor carga fuentes con elementos HTML; por eso `GET /editor/projects/media` acepta el token en la consulta, valida que el proyecto declare la fuente y entrega video proxy e imagen original.
- **Descartadas**: usar las pruebas de matrices como medida de paridad, porque no comprueban los píxeles; construir un visor temporal solo para el e2e, porque duplicaría el flujo que valida la app.
- **Cómo revertir**: revertir los commits de T5 que agregan `preview/`, `GET /editor/projects/media` y esta ficha; conservar el render de servidor y mover el e2e a la fase de cierre solo si ya existe otro canvas funcional.
- **Cómo comprobarla**: `bunx vitest run tests/unit/src/features/editor/preview --maxWorkers=1`; en T6, ejecutar `editor/parity-preview-export.e2e.ts` con los fixtures de `parity-*.json`, cinco tiempos por transición y SSIM >= 0,95.
- **Pendiente**: integrar y ejecutar el e2e durante T6 antes de completar T7.
