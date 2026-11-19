# 001: la duración de la salida no coincide con la pedida (narración y música)

- **Qué**: `music --duracion 15` sale en 12.2 s (`acestep-lofi-chill.wav`, tras recortar el silencio). `narration tts` con «Prueba de la spec uno.» sale en 1.0 s. Los dos resultados se repiten en `dev` (base): música 12.0 s, narración 1.1 s con el mismo comando y voz.
- **Por qué no se hizo**: el criterio de 03 §2.7 (15 s ± 0,5 s) no lo cumple ni el código de `dev`. Es comportamiento previo (recorte de silencio en música, duración del TTS), no de esta refactorización. Corregirlo cambia la salida de audio, así que es decisión del usuario.
- **Cuándo**: antes de publicar el lote; no bloquea el paso a `main` de la 001.
- **Quién**: usuario (decide si la duración pedida es el destino final o el recorte ya basta) y agente, si el usuario quiere cambiarla.
- **Qué la cierra**: decisión del usuario sobre el criterio de duración; o un test de caracterización que fije la duración real y un cambio de comportamiento aprobado. Escucha: `out/music/spec-001/acestep-lofi-chill.wav` y `out/narration/spec-001/prueba.wav` (las dos del principal).
