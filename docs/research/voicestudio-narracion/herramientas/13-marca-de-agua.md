# Marca de Agua de IA (AI Watermark)

> Investigación del 2026-11-15. Qué marca de agua aplica VoiceStudio al audio sintético (AudioSeal invisible, tono audible y logo en video), cómo se activa y se verifica, y qué implica para publicar videos. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

VoiceStudio tiene tres capas, definidas en `backend/services/watermark.py` **(leída)**:

| Capa | Técnica | Default | Dónde se aplica |
| :--- | :--- | :--- | :--- |
| **Invisible** | **AudioSeal** (Meta): red neuronal que suma un residuo imperceptible a 1–2 kHz con un mensaje de **16 bits** (`OMNI_MESSAGE` = "OM" en ASCII) | **Encendida** (`watermark.invisible`, default `True`) | Todo audio sintético que sale de la app, vía la función única `mark_synthetic()` |
| **Audible** | Tono de marca: acorde ascendente C5→E5→G5 de 0,4 s al 15 % de amplitud + 100 ms de silencio, antepuesto | Apagada (`watermark.visible_audio`, default `False`) | Pensada para exportaciones finales (ver §6: **conflicto**) |
| **Visual** | Logo `docs/logo.png` de 64 px abajo a la derecha, con *fade out* a los 5 s, vía `ffmpeg -filter_complex` | **Encendida** (`watermark.visible_video`, default `True`) | Solo `POST /export` de un `.mp4` (`backend/api/routers/exports.py` L65-95) |

* **Por qué existe:** el docstring de `mark_synthetic` cita el **EU AI Act art. 50(2)** (aplicable desde 2026-08-02), que exige una marca legible por máquina en audio sintético, y afirma que el art. 2(12) la excluye de la exención open source **(leída, `watermark.py` L424-431)**. La interpretación legal es del proyecto: **no verificado** con fuente jurídica.
* **Licencia de AudioSeal:** `pyproject.toml` la declara MIT, "~5 ms por segmento en CPU", dependencia obligatoria (`audioseal>=0.1.3`) **(leída)**. La licencia de los pesos (`facebook/audioseal` en HF) **no verificado**.
* **Corre en CPU** y no compite por VRAM: se movió fuera del pool de GPU porque serializaba la siguiente generación en máquinas de 1 worker (CHANGELOG, #1190) **(leída)**.

---

## 2. Cómo Se Usa

### 2.1 Activar o desactivar

* **UI:** Settings → Privacy → *Invisible watermark*. Solo aparece si el backend reporta AudioSeal disponible, y afecta solo al audio generado después del cambio (`docs/electron-privacy.md` L9, L27; CHANGELOG #1308) **(leída)**.
* **API** (parámetros por *query string*; escribir exige credencial de administrador por `require_consumer_reads_admin_writes`) **(leída, `backend/api/routers/watermark.py`)**:

```bash
# Ver estado
curl http://127.0.0.1:3900/watermark/status
# → {"invisible_enabled": true, "visible_audio_enabled": false,
#    "visible_video_enabled": true, "audioseal_available": true}

# Apagar la invisible y el logo de video
curl -X POST "http://127.0.0.1:3900/watermark/settings?invisible=false&visible_video=false"
```

### 2.2 Verificar (detectar)

```bash
curl -X POST http://127.0.0.1:3900/watermark/detect -F "file=@narracion.wav"
# → {"is_watermarked": true, "confidence": 0.99, "message_bits": "0100111101001101",
#    "is_omnivoice": true, "source": "VoiceStudio"}
```

* Formatos aceptados: `.wav .mp3 .flac .ogg .m4a .aac .opus`; otro da 400. Sin AudioSeal, 503 **(leída, `watermark.py` router L36-46)**.
* La detección corre por trozos de 30 s y se queda con **el trozo de mayor confianza**: un montaje donde solo una parte es de VoiceStudio igual se detecta **(leída, `detect_watermark` L687-699)**.
* `is_watermarked` = confianza > 0,5. `is_omnivoice` exige que los 16 bits coincidan exactamente con "OM" **(leída)**.
* El notebook de Colab (celda 14) hace la prueba de referencia: un clip generado da confianza alta y un tono `ffmpeg sine=440` da negativo **(leída, `notebooks/OmniVoice_Studio_Colab.ipynb`)**.

### 2.3 Usarlo desde Python (sin la app)

La API interna es reutilizable fuera de la app (requiere `torch`, `torchaudio`, `audioseal`):

```python
from services.watermark import embed_watermark, detect_watermark
marcado = embed_watermark(waveform, 24000)         # mismo shape
resultado = detect_watermark(marcado, 24000)        # dict con confidence
```

Fuente: docstring de `backend/services/watermark.py` L11-18 **(leída)**. El código es AGPL: copiarlo a `narration/` contagia la licencia; reimplementar contra `audioseal` directamente no.

---

## 3. Opciones y Parámetros

| Opción | Valores | Default | Efecto | Fuente |
| :--- | :--- | :--- | :--- | :--- |
| `watermark.invisible` (pref) | bool | `True` | AudioSeal en todo audio nuevo | `watermark.py` L390-392 **(leída)** |
| `watermark.visible_audio` (pref) | bool | `False` | Tono de marca antepuesto | L404-406 **(leída)** |
| `watermark.visible_video` (pref) | bool | `True` | Logo en `/export` de `.mp4` | L409-411 **(leída)** |
| `force=True` (interno) | bool | `False` | Marca aunque el usuario la apague. Lo usan los *persona bundles* y la telefonía agéntica | L452, `docs/persona-format.md` **(leída)** |
| `OMNIVOICE_PRELOAD_WATERMARK` | `0`/`1` | precarga solo si ya está en caché | `1` permite descargar el checkpoint al arrancar; `0` desactiva la precarga | `docs/electron-privacy.md` L219-223; CHANGELOG **(leída)** |
| `AUDIOSEAL_CACHE_DIR` / `XDG_CACHE_HOME` | ruta | `~/.cache/audioseal` | Dónde vive el checkpoint | `_audioseal_checkpoint_path` L275-302 **(leída)** |
| `_CHUNK_SECONDS` | constante | 30 | Trozo de proceso, acota memoria (#1045) | L96 **(leída)** |
| `_GENERATOR_RETRY_SECONDS` | constante | 600 | Espera tras un fallo de carga | L71 **(leída)** |

---

## 4. Ejemplos

| Caso | Pasos | Resultado esperado |
| :--- | :--- | :--- |
| Comprobar que un reel lleva marca | Exportar el `.mp4` final → `ffmpeg -i reel.mp4 -vn -ac 1 reel.wav` → `POST /watermark/detect` | `is_omnivoice: true` si la voz salió de VoiceStudio y la mezcla no la destruyó |
| Video sin logo de VoiceStudio | `POST /watermark/settings?visible_video=false` antes de exportar | `/export` copia el `.mp4` sin overlay |
| Narración sin marca invisible | Settings → Privacy → apagar | Afecta solo lo generado después; lo anterior sigue marcado |
| Auditar un archivo ajeno | `POST /watermark/detect` | `source: "unknown"` si hay marca AudioSeal con otro mensaje, o `is_watermarked: false` |

---

## 5. Tips y Trucos

* **Dejar margen de pico.** Si la toma llega cerca de 0 dBFS, sumar el residuo la saturaría y el recorte borraría la marca. VoiceStudio atenúa la voz y vuelve a marcar hasta 3 veces (#3468) **(leída, L613-630)**. En un pipeline propio conviene normalizar a ≤ −1 dBTP **antes** de marcar y no tocar la ganancia después.
* **Marcar al final, no al principio.** La marca se aplica "justo antes de que el audio salga de la app" **(leída, L426-428)**. Si después se mezcla con música, se comprime o se cambia el tempo, hay que volver a verificar.
* **El residuo se resamplea a la tasa original:** AudioSeal trabaja a 16 kHz, pero solo el residuo vuelve a 24/48 kHz y se suma; la voz conserva sus agudos (#2252) **(leída, `_embed_chunk` L548-556; `electron-privacy.md` L204-207)**.
* **Se quitó el DC offset.** El generador de 16 bits deja un sesgo de ~−7 LSB que se notaba en las pausas; ahora se resta la media del residuo (#2818) **(leída, `_remove_dc` L534-545)**.
* **Falla abierto:** si AudioSeal no carga, el audio sale **sin marca y sin error** (solo un warning en el log). Para garantizar procedencia hay que verificar con `/watermark/detect`, no asumir **(leída, L640-645; `electron-privacy.md` L219)**.

---

## 6. Problemas Conocidos

| Problema | Estado | Fuente |
| :--- | :--- | :--- |
| `/v1/audio/speech` salía sin marca; se centralizó en `mark_synthetic` y un test exige que toda ruta la llame | Resuelto | [#1169](https://github.com/debpalash/VoiceStudio/issues/1169) (CHANGELOG) **(leída)** |
| `torch.compile` en el primer *embed* fallaba en macOS y el audio salía sin marca (10/10 tomas); ahora corre en modo eager | Resuelto | [#1615](https://github.com/debpalash/VoiceStudio/issues/1615) **(leída)** |
| Pico de varios GB de RAM al marcar audio largo de una vez; ahora va por trozos de 30 s | Resuelto | [#1045](https://github.com/debpalash/VoiceStudio/issues/1045) **(leída)** |
| Cada render esperaba ~3 min de timeout si el checkpoint no se podía descargar | Resuelto: reintento cada 10 min | [#2933](https://github.com/debpalash/VoiceStudio/issues/2933) **(leída)** |
| La precarga nunca encontraba el checkpoint en caché (nombre de archivo equivocado) | Resuelto | [#2818](https://github.com/debpalash/VoiceStudio/issues/2818) **(leída)** |
| **`apply_audio_brand` (tono audible) no se llama desde ningún router del backend**: la preferencia existe y se expone en `/watermark/status`, pero no tiene efecto | **conflicto** (doc/API vs código) | `rg apply_audio_brand backend/` solo encuentra la definición **(leída)** |
| Chatterbox ya trae su propia marca (PerTh); combinarla con AudioSeal es "doble marca" sin probar | Abierto (por eso no integran Chatterbox en el proceso principal) | `docs/competitive-analysis.md` L1427-1429 **(leída)** |

---

## 7. Qué Dice la Comunidad

* **Robustez de AudioSeal frente a MP3/AAC: conflicto entre papers (A).** *Watermarking across Modalities* ([arXiv 2502.05215](https://arxiv.org/pdf/2502.05215)) le da AUC ~1,00 con MP3 y 0,97 de media; *XAttnMark* ([arXiv 2502.04230](https://arxiv.org/pdf/2502.04230)) dice que AudioSeal "sufre" con MP3/AAC, aunque mide *atribución* y no detección **(snippet)**.
* **Punto débil: códecs neuronales y ataques adversarios (A).** AudioMarkBench ([arXiv 2406.06979](https://arxiv.org/pdf/2406.06979)) encuentra que la compresión neuronal es el caso más difícil; con EnCodec la detección cae a ~0,50 en un escenario **(snippet)**.
* **Usuarios vs prensa (C).** El análisis competitivo del propio repo dice que los usuarios hobby "prefieren sin marca" y que nadie lo pide, pero la prensa lo elogia y es un activo de cumplimiento normativo **(leída, `competitive-analysis.md` L1360)**.

---

## 8. Qué Sirve para social-videos

1. **Hoy ya sale audio marcado de un motor:** Chatterbox (todas sus variantes) aplica `perth.PerthImplicitWatermarker` en cada generación **(leída, `narration/.venv-chatterbox/.../chatterbox/mtl_tts.py` L175, L354)**. Qwen3-TTS y OmniVoice en `narration/` no marcan. El resultado es una procedencia inconsistente entre motores.
2. **Propuesta, si se quiere procedencia uniforme:** un paso opcional `--marca` en `narration/tts.py` que llame a `audioseal` directamente (MIT, CPU, sin VRAM), marque **después** de normalizar y antes de escribir el WAV, y un `--verificar` que corra el detector. Reimplementarlo evita copiar código AGPL. Para Chatterbox habría que decidir: ¿PerTh solo, o PerTh + AudioSeal (sin probar)?
3. **Verificar después de la mezcla final**, no solo sobre la voz suelta: la música de `music/`, el AAC del MP4 y los cambios de velocidad de las plataformas pueden degradar la marca. El criterio práctico es correr el detector sobre el audio extraído del video final.
4. **La marca de agua no reemplaza las etiquetas de las plataformas.** YouTube, TikTok y Meta piden declarar contenido sintético realista con su propio rótulo **no verificado** (no se revisaron sus políticas en esta sesión). El art. 50 del AI Act aplica a quien despliega en la UE; para una cuenta que publica desde Chile o México su alcance **no verificado**.
5. **Licencias:** marcar un audio de OmniVoice no cambia su licencia. Los pesos siguen siendo **CC-BY-NC** (no comercial) aunque `pyproject.toml` diga que "el modelo OmniVoice es Apache-2.0": **conflicto**, porque Apache-2.0 cubre el código y `model_licenses.json` separa los pesos no comerciales **(leída)**. Para publicidad, la marca no habilita el uso comercial.
6. **El logo de video (activo por defecto)** solo importa si se exporta video desde VoiceStudio. En este repo el video se arma fuera, así que no aplica.
