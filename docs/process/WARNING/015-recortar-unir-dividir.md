# 015: recortar, unir y dividir (T6)

**Qué se decidió.**

- **Recortar `remove`** reusa `clean/render.py` (D-5): cada tramo lleva un fundido de 15 ms y se une sin solaparse. Así la duración es exacta: 10 s menos 2 s dan 8,000 s. Un `acrossfade` le quitaría 15 ms por unión.
- **Recortar `keep`** pone los fundidos pedidos (`afade` o `fade`, con `t=in` desde 0 y `t=out` antes del final).
- **Formato de salida**: un audio recortado o unido sale en **WAV** (PCM 24 bits); un video, en **MP4** (H.264 y AAC a 192 kbps). El formato de la fuente no se conserva: para otro códec está el conversor (T2).
- **Unir con crossfade** normaliza los clips al primer clip (tamaño, fps, SAR y formato yuv420p) y al audio a 48 kHz estéreo. El `xfade` empieza `crossfade` antes del final del anterior, y el `acrossfade` queda alineado. Sin crossfade, `concat`.
- **`mixed_kinds`** se da en la validación del servicio (con `ffprobe` de cada archivo) y también en `concat()`.
- **Dividir recodifica cada parte** con su propio `-ss` y `-t`. El muxer de segmentos corta en la frontera del paquete de audio: con PCM de 8 kHz la primera parte de 60 s salió de 60,032 s. Por eso cada parte se saca aparte. `copy` queda como opción de Avanzado (el corte cae en un keyframe).
- **Nombres**: las partes son `<nombre>-01.<ext>`, `-02`, …, como pide D-5.

**Verificado** (`media/test_edit.py`, 8 pruebas con ffmpeg real):

- AC-7: `remove` de 2–4 s en 10 s deja 8,00 s ± 20 ms. `keep` con fundido de 0,5 s: el RMS de los primeros 50 ms queda al menos 20 dB por debajo del segundo 1.
- AC-8: tres videos de 640×360, 320×240 y 854×480 con crossfade de 1 s: sale 640×360 y dura 7,0 s ± 1 cuadro. Audio con video: `mixed_kinds`.
- AC-9: 25 min cada 10 min dan 10, 10 y 5 min ± 20 ms. Marcas `[60, 120]`: 3 partes, la primera de 60 s y la última de 1380 s.
- Video `remove`: resolución del original y la duración menos el tramo.

**Límite conocido.** La AC-9 se prueba con 25 min de silencio a 8 kHz: el resultado depende de la duración, no del contenido, así que el tiempo de la prueba queda bajo. La prueba de «sin clic» de AC-7 no mide el clic: el fundido de 15 ms lo evita por construcción.

**Dónde.** `server/src/content_studio/media/edit.py` (`trim`, `concat`, `split`, y el CLI `edit`), `services/media_{trim,concat,split}.py`, y dos claves de error nuevas (`mixed_kinds`, `invalid_split`) en los tres catálogos.
