# Preparar una Referencia Ajena para CosyVoice 3

> Investigación del 2026-11-17. La receta paso a paso, verificada en esta máquina, para convertir una fuente libre (un capítulo de LibriVox o una donación de Kyutai) en una referencia que clona bien con CosyVoice 3, y qué automatiza `narration/voces.py`. Complementa [voicestudio-narracion/11](../voicestudio-narracion/11-audio-de-referencia.md), que trata la grabación propia. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **medido**.

---

## 1. Lista de Control

| # | Paso | Por qué | Evidencia |
| :--- | :--- | :--- | :--- |
| 1 | Verificar la **licencia del ítem** (no la del dataset derivado) y guardar URL, fecha y tramo | La procedencia es la única defensa ([02](02-derechos-copyright-y-voz.md) §6) | **(leída)** |
| 2 | Evitar lectores fallecidos, figuras públicas y locutores identificables | AB 1836, derecho a la voz | **(snippet)** |
| 3 | Bajar el original con mejor calidad (VBR o 128 kbps, no `_64kb`) | Los artefactos del códec se clonan | C **(snippet)** |
| 4 | Saltar el preámbulo de LibriVox (20–30 s) | Tiene otra entonación; en Voice-Zero hasta se coló como "voz" | **medido** ([05](05-donaciones-cc0-kyutai-y-voice-zero.md) §3.1) |
| 5 | Elegir **8.5–12 s de frases completas**, sin diálogo ni voces de personajes, con huecos < 0.7 s | Duración común a los motores; CosyVoice rechaza > 30 s | A/B ([08](08-practicas-de-la-comunidad.md) §3.1) |
| 6 | Recortar **sin procesar**: mono, frecuencia original, PCM 24 bits | El denoise baja la similitud | A |
| 7 | Transcribir con marcas por palabra y **corregir contra el texto fuente** | CosyVoice 3 necesita la transcripción exacta en zero-shot | B |
| 8 | Normalizar **solo la ganancia** a −18 LUFS, con pico real ≤ −3 dBTP (limitador solo en los transitorios) | Criterio de la guía de grabación; `referencia.procesar()` | **medido** |
| 9 | Escuchar 30 s y decidir el acento | Ninguna fuente declara el país del lector | — |
| 10 | Clonar dos textos de prueba y medir WER, SIM y UTMOS | Elegir con números ([10](10-pruebas-en-gpu.md)) | A |

---

## 2. Comandos

### 2.1 LibriVox

```bash
# 1. Licencia y archivos del ítem
curl -s https://archive.org/metadata/angelina_1109_librivox | python -c "import json,sys; d=json.load(sys.stdin); print(d['metadata'].get('licenseurl')); [print(f['name']) for f in d['files'] if f['name'].endswith('.mp3')]"

# 2. Bajar el capítulo
curl -L -o cap.mp3 https://archive.org/download/angelina_1109_librivox/angelina_01_delgado.mp3

# 3. Ventana sin preámbulo para transcribir (60 s → 300 s)
ffmpeg -ss 60 -t 240 -i cap.mp3 -ac 1 ventana.wav
whisper ventana.wav --model medium --language es --word_timestamps True --output_format json

# 4. Recorte final, sin procesar (inicio y duración salen del paso 3, con 0.25 s de margen)
ffmpeg -ss 66.99 -t 11.66 -i cap.mp3 -ac 1 -c:a pcm_s24le ref.wav
```

### 2.2 Kyutai

```bash
curl -L -o ref.wav https://huggingface.co/kyutai/tts-voices/resolve/main/voice-donations/Yesid.wav
whisper ref.wav --model large-v3-turbo --language es   # la transcripción va en ref.txt
```

### 2.3 Usarla con `tts.py`

```bash
python cli.py narration tts --modelo cosyvoice3 --ref ref.wav --texto "..."   # ref.txt al lado, obligatorio
```

O, mejor, agregar la voz a `narration/voces/catalogo.json` y dejar que `voces.py` haga todo ([11](11-catalogo-y-aplicacion.md)).

---

## 3. Errores que Aparecieron al Automatizarlo **medido**

| Problema | Síntoma | Arreglo |
| :--- | :--- | :--- |
| Los segmentos de whisper no coinciden con las frases | El tramo empezaba en "los acontecimientos notables. Período…" o "deslizarse como un felino…" | Armar las frases con `word_timestamps` y cortar solo en `.` `?` `!` |
| Exigir que el segmento anterior termine en punto | Tres fuentes quedaron "sin tramo" | Trabajar con frases, no con segmentos |
| Whisper `medium` en un clip procesado | Transcripción vacía (Voice-Zero, Cori Samuel) | Probar `large-v3-turbo` y escuchar el clip |
| Clips de Kyutai de 10 s fijos | Empiezan o terminan a mitad de palabra (John_Triguero, Andrea) | Se usan enteros: clonaron con WER ≤ 0.10. Si se nota en la salida, recortar a frases completas (aunque queden de 5–6 s) |
| Piper genera 15 s con el texto del kit | Fuera del rango de 8–12 s | Acortar el texto |
| Piper satura | Pico real +0.2 dBTP | `referencia.procesar()` lo corrige; Piper no limita su salida |
| Whisper y WavLM en la GPU con CosyVoice | ~4 min por clip en vez de ~15 s: la VRAM se desborda a la RAM compartida | Un modelo a la vez: generar, liberar y después evaluar (`voces.py`) |
