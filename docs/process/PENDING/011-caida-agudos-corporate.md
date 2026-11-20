# 011: pista corporate-minimal v2 pierde los agudos desde ~19.5 s

- **Qué**: en la corrida real de T9 (`studio music --model acestep --style lofi-chill corporate-minimal --variants 2 --duration 30 --evaluate --retries 1`, carpeta `out/music/2026-11-20-1-lofi-chill-corporate-minimal/`), `acestep-corporate-minimal-v2.wav` baja la energía por encima de 6 kHz de −33,6 dB (18–19 s) a −54,8 dB (19–20 s) y queda cerca de −60 dB hasta el final. Sin silencios (0 tramos de 0,3 s bajo −50 dB). Las otras tres pistas no muestran ese escalón. Detectado por el espectrograma del agente `image-reader` y confirmado con `astats`.
- **Por qué no se hizo**: es un defecto de contenido del motor, no del código, y el criterio «sin cortes» lo decide la escucha. No se regeneró ni se cambió nada.
- **Cuándo**: antes de usar esa pista en un video; no bloquea el merge de la 011.
- **Quién**: usuario (escucha). El agente la regenera con `studio music --style corporate-minimal --variants 2 --duration 30` si el usuario lo pide.
- **Qué la cierra**: la escucha de `acestep-corporate-minimal-v2.wav` (o su regeneración) y la decisión de usarla o descartarla.
