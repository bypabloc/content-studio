# 018: paridad del compositor con el render

- **Contexto**: AC-5 compara el visor WebGL con `GET /editor/projects/frame` en cinco instantes y ocho transiciones.
- **Elegida**: el e2e captura el canvas sin guías ni asas; usa muestras a 24 fps para que 4,75 s coincida con un cuadro. Las curvas de `fadeblack`, `fadewhite`, `wipeleft`, `wiperight` y `circleopen` siguen las fórmulas de `xfade` de [FFmpeg](https://github.com/FFmpeg/FFmpeg/blob/master/libavfilter/vf_xfade.c).
- **Hallazgo**: las primeras comparaciones incluían controles del visor o mostraban que el compositor usaba pesos aproximados. La prueba final pasa en los cinco tiempos con SSIM >= 0,95.
- **Descartadas**: usar pruebas de matrices como medida de paridad, porque no comparan píxeles; construir un visor temporal, porque duplicaría el flujo de la app.
- **Cómo revertir**: revertir los cambios del compositor y los fixtures AC-5, sin revertir el render de servidor.
- **Cómo comprobarla**: `bunx vitest run tests/unit/src/features/editor/preview/transitions.test.ts`; `bunx playwright test editor/parity-preview-export.e2e.ts --workers=1 --trace=off` desde `tests/e2e`.
- **Pendiente**: cerrado en T6; mantener la prueba en el gate e2e de T7.
