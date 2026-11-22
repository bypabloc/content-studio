# 013: las regiones de la onda usan la duración del análisis

- **Contexto**: la revisión dibuja cada corte como región sobre la onda con la `duration` del análisis (WaveSurfer 8 la usa
  como duración de la onda). En una captura de prueba, las regiones salieron desplazadas: el fixture de la API simulada
  trae `duration: 60`, y los archivos de prueba miden 32,7 s (audio) y 40 s (video). La regla de la línea de tiempo sí
  sigue la duración del medio.
- **Elegida**: no se cambia el componente. La duración del análisis sale del mismo `ffprobe` que el archivo, así que en
  producción coinciden. Las capturas fijan la duración del análisis igual a la del archivo.
- **Medido** (DOM, fracción del ancho de la onda; esperado = tiempo / duración):
  - Audio de 32,7 s: corte 1 en 0,3058 (10/32,7) y corte 2 en 0,9174 (30/32,7); anchos 0,0765 y 0,0367.
  - Video de 40 s: corte 1 en 0,25 (10/40) y corte 2 en 0,75 (30/40); anchos 0,0625 y 0,03.
- **Descartada**: usar la duración decodificada del medio en el componente. Cambiaría la fuente de verdad sin un caso real
  que lo pida.
- **Cómo revertir**: no aplica (sin cambio de código por esta decisión).
- **Pendiente**: si un archivo real tuviera duración distinta entre `ffprobe` y el medio, las regiones se correrían. Con los
  archivos de prueba no pasa; la revisión del usuario lo confirma.
