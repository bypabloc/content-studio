# 018: paridad del compositor con el render

- **Contexto**: AC-5 compara el visor WebGL con `GET /editor/projects/frame` en cinco instantes y ocho transiciones.
- **Elegida**: el e2e captura el canvas sin guías ni asas; usa muestras a 24 fps para que 4,75 s coincida con un cuadro. Las curvas de `fadeblack`, `fadewhite`, `wipeleft`, `wiperight` y `circleopen` siguen las fórmulas de `xfade` de [FFmpeg](https://github.com/FFmpeg/FFmpeg/blob/master/libavfilter/vf_xfade.c).
- **Hallazgo**: las primeras comparaciones incluían controles del visor o mostraban que el compositor usaba pesos aproximados. La prueba final pasa en los cinco tiempos con SSIM >= 0,95. El primer logo sintético de T8 tenía alfa 0 en todos sus píxeles y ambos compositores lo descartaban; al corregir el PNG RGBA, image-reader confirmó su aparición sin halo.
- **Medición T8**: el proyecto de 5,5 s se exportó a MP4 H.264 NVENC (5,500 s) y WebM VP9/Opus (5,508 s), ambos a -21,6 LUFS. Siete pares de cuadro exacto del server y MP4 dieron SSIM entre 0,974366 y 0,997220; image-reader confirmó el logo, la transición y el zoom. Los SHA-256 de las tres fuentes coinciden antes y después.
- **Escala AC-6**: 40 clips, 60 s, 720p/30 fps; render 6,18 s y grafo `.filter` de 26 395 bytes.
- **Descartadas**: usar pruebas de matrices como medida de paridad, porque no comparan píxeles; construir un visor temporal, porque duplicaría el flujo de la app.
- **Cómo revertir**: revertir los cambios del compositor y los fixtures AC-5, sin revertir el render de servidor.
- **Cómo comprobarla**: `bunx vitest run tests/unit/src/features/editor/preview/transitions.test.ts`; `bunx playwright test editor/parity-preview-export.e2e.ts --workers=1 --trace=off` desde `tests/e2e`.
- **Pendiente**: cerrado en T6; mantener la prueba en el gate e2e de T7.
