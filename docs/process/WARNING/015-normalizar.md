# 015: normalizar a LUFS en dos pasadas (T5)

**Qué se decidió.**

- **Dos pasadas, como pide D-4.** La primera mide con `loudnorm` (JSON). La segunda aplica en lineal con esas medidas (`measured_*`, `linear=true`). El antes y el después salen de `ebur128`, no de los números de loudnorm.
- **Presets**: `youtube` -14, `podcast` -16, `broadcast` -23, `custom` con su valor. LRA 11 en los cuatro.
- **Techo de pico según el códec de salida** (`true_peak_for`, T9): −1 dBTP para WAV y FLAC; **−2 dBTP para los formatos con pérdida** (MP4, MOV, MKV, M4A, WebM, MP3). El codificador sube el pico después de `loudnorm`: en el video de prueba, con −1 dBTP, la salida quedó en −0,8 dBFS (incumplía la regla de D-4); con −1,5, en −1,3 y −14,9 LUFS; con −2, en −1,6 y −15,4 LUFS. Se eligió −2 por el margen, que el sobrepico depende del material. El costo es la sonoridad del video: −1,4 LU respecto de −14 en `youtube`. Si el usuario prefiere −1,5 dBTP, es un cambio de una constante (`LOSSY_TRUE_PEAK`), con su prueba.
- **«Mejorar voz»**: la cadena fija de D-4 (`highpass`, `deesser`, `acompressor`) va antes de loudnorm en las dos pasadas. Es la única que propone la spec; no hubo otra cadena que elegir.
- **Códec de salida con bitrate fijo** (`media/normalize.py`, `audio_args`): AAC 192k para MP4, MOV, MKV y M4A; Opus 160k para WebM; MP3 192k. WAV y FLAC conservan su códec sin pérdida. El valor por defecto del codificador AAC movió el nivel: con un ruido rosa a -16 LUFS salió a -15,3 LUFS y pico -1,5 dBTP. Con 128k, 192k o 320k salió a -16,1, -16,1 y -16,0.
- **Video**: `-map 0:v? -c:v copy`. Solo el audio cambia; el hash de los paquetes de video se compara en la prueba.
- **Reference**: una ruta dentro de `paths.references_dir()` da `reference_protected`. Los códigos `reference_protected` y `unknown_preset` tienen su texto en `es`, `en` y `pt`.

**Verificado.**

- Fixture de AC-6: ruido rosa con `seed` a -30,0 LUFS (un tono puro no sirve: loudnorm cae a dinámico, aunque mide bien). Normalizado a `podcast`: -16,0 LUFS (±0,5 OK) y pico -2,2 dBTP. Modo lineal.
- Voz real (narración de `out/` del checkout principal, solo como entrada): lineal, -16,1 → -15,9 LUFS, pico -1,4 dBTP.
- Video con ruido rosa y `testsrc2`: hash de paquetes de video igual; audio a -16 ± 0,5.
- `reference_protected` y los presets, con pruebas unitarias.
- Corrida real (T9, CLI, medidas con `ebur128`): narración 01 y música `acestep-lofi-chill`, a `podcast` (−16,0 LUFS en los cuatro, con y sin «mejorar voz») y a `youtube` (entre −14,1 y −14,7 LUFS). Pico −1,0 dBFS en los WAV. Modo lineal solo en la narración a `podcast`; el resto, dinámico. El reporte de cada trabajo está en `out/media/…-media-normalize/result.json`.

**Diferido.** La REFACTOR del plan (`narration/audio.py`, la masterización `--master voice`) repite la misma idea de dos pasadas, pero con TP -1,5 y remuestreo a la frecuencia nativa. Migrarla cambia la salida de la narración, así que va en un commit aparte, con las fixtures de caracterización de la narración como prueba.

**Dónde.** `server/src/content_studio/media/normalize.py`, `services/media_normalize.py`, `messages/{es,en,pt}.json` (dos claves de error), y las pruebas `media/test_normalize.py` y `services/test_media_normalize.py`.
