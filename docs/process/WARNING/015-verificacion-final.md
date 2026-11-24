# 015: verificación final (T9)

**Qué se decidió al correr.**

- **Insumos.** El video de la 013 no está en el checkout principal. Se generó `tmp/spec-015/charla.mp4`: 40 s, 1920×1080, patrón `testsrc2` y, como pista, la voz de la narración 01 de `out/` (solo lectura). El audio de 3 min (`voz-3min.wav`) son cuatro narraciones y la música `acestep-lofi-chill`.
- **Por la API y la CLI.** Recortar, unir y dividir, por `studio serve` con token local y HTTP. Convertir, normalizar y GIF, por la CLI: son el mismo servicio.
- **Manual y seguir a la persona no están en la CLI.** Se corren con `submit.execute` (el mismo servicio que la API) desde un script temporal. El manual elige la franja derecha (x = 0,55).
- **Seguir a la persona sin caras.** El análisis devuelve 0,5 en los 200 cuadros, así que el encuadre cae en el centro. AC-12 (la cara en el tercio central) queda sin probar con una cara real: va al PENDING `015-foto-de-prueba`.
- **Techo de pico con pérdida: −2 dBTP.** Ver [015-normalizar](015-normalizar.md). Con −1 dBTP el video salió a −0,8 dBFS.
- **Salidas copiadas al checkout principal.** `out/spec-015/` (gitignored): al cerrar el worktree se borran sus `out/` y `tmp/`.

**Medidas.**

| Operación | Resultado |
| :--- | :--- |
| Convertir (5 archivos) a MP3 V2, FLAC y OGG Opus | Los 15 `done`. FLAC y Opus con la duración de la entrada (±0,01 s). MP3 con +0,07 s de relleno de LAME |
| Redes 1080×1920, 30 fps, 40,02 s | Los cinco modos, h264. Cuadros en `cuadros/reels-<modo>-{2,12,22}.png` |
| GIF de 5 s | 480×270, 15 fps, 75 cuadros, 5,0 s, 1,08 MB |
| Recortar, quitar 10–20 s de 40 s | 30,00 s |
| Unir 3 clips de 10 s, fundido de 1 s | 28,08 s, audio AAC estéreo 48 kHz |
| Dividir cada 60 s un audio de 180 s | 3 partes de 60,00 s |
| Normalizar (WAV, 8 trabajos) | Pico −1,0 dBFS; `podcast` −16,0 LUFS; `youtube` entre −14,1 y −14,7 LUFS |
| Normalizar video, −1 dBTP (antes del ajuste) | −14,6 LUFS, pico −0,8 dBFS: incumple D-4 |
| Normalizar video, −2 dBTP (final) | −15,4 LUFS, pico −1,6 dBFS |

- **Clics en la unión.** El salto máximo entre muestras en los cruces (1 361 y 2 571) está dentro del rango de las ventanas sin cruce (2 185 a 4 408). El espectrograma no muestra bandas anómalas.
- **Errores.** Formato inexistente: exit 2 (argparse, en inglés). Audio con video en `concat`: exit 2, «No se puede unir audio con video en una misma unión.». Referencia de voz en `normalize`: exit 2, «Este archivo es una referencia de voz: no se normaliza.».

**Batería.** `pytest` de medios, servicios y `test_face_track.py` con `-m local`: 227 pasan y 1 se salta (la foto). e2e: 49 de 49. `guard-tdd`: pasa. El gate `all` pasa.
