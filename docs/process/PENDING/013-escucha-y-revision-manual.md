# 013: escucha y revisión manual del limpiador

- **Qué falta**: el usuario escucha los resultados y revisa la UI real. Las capturas de la revisión salieron de la API
  simulada (e2e), no de la app instalada.
- **Qué escuchar** (rutas en `out/clean/`, la carpeta de cada trabajo):
  - Video limpio `clean.mp4` de la corrida 16 (charla de prueba de 232 s): que los cortes suenen naturales.
  - Audio limpio `clean.wav` de las carpetas 24 y 26 (narración con silencios añadidos a mano; el informe dice 27,678 s
    y 27,248 s).
  - Subtítulos `subtitles.srt` de cada salida: que sigan a la voz.
- **Qué decidir**: si el margen de 150 ms y el umbral de -50 dB recortan consonantes suaves. Si hay que cambiarlos, son dos
  números (`--padding`, `--min-gap`) y la spec los acepta.
- **Revisión manual de la UI**: revisar los cortes en la app (desactivar uno, arrastrar un borde, cambiar el hueco a 700
  ms, renderizar) con video y con solo audio, en claro y en oscuro.
- **Exportaciones**: `cuts.edl` y `cuts.xml` no se probaron en DaVinci Resolve ni en Premiere; validados en formato con
  pruebas. Si se instala un editor, importarlos y anotar el resultado aquí.
- **Cuándo**: después del merge a `dev`; no bloquea el merge.
