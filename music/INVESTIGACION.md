# Investigación: modelos de música local para RTX 4060 Laptop (8 GB)

Fecha: 2026-10-04. Objetivo: música de fondo **instrumental** (lofi y otros estilos) generada en local, open source, que entre en una RTX 4060 Laptop de 8 GiB (compute capability 8.9; ~6,9 GiB libres con el escritorio abierto).

> El filtro inicial pedía soporte de español. Después se aclaró que solo interesa el ritmo (sin voz), así que **el idioma no es criterio**. Los modelos solo instrumentales (MusicGen, Stable Audio Open) vuelven a ser candidatos válidos.

## Elegidos

| Modelo | Publicado | Variante para 8 GB | VRAM | Licencia | Instrumental | Opinión de la comunidad |
|:--|:--|:--|:--|:--|:--|:--|
| **ACE-Step 1.5** | ene 2026 | DiT 2B **turbo** (8 pasos) + LM `acestep-5Hz-lm-0.6B`, backend PyTorch, con offload a CPU | < 4 GB según el proyecto; ~6 GB medido (ver README) | MIT | Sí, con más de 1000 estilos e instrumentos y LoRA a partir de pocas canciones | La más recomendada. En SongEval supera a Suno v5 según el proyecto, genera una canción en menos de 10 s en una 3090 y se valoran mucho la licencia y el LoRA |
| **HeartMuLa 3B** | ene 2026 | 3B en bf16 con `lazy_load` (carga el LM, lo descarga y luego carga el codec) | Las fuentes dicen ~6,2 GB de pico, pero **medí 12,67 GB** en el LM: desborda a la RAM compartida de WSL y por eso es lento (ver README) | Apache 2.0 | Sí, con secciones `[Instrumental]` y hasta 240 s | Su paper reporta la menor tasa de error de fonemas en las letras de todos los idiomas que evaluó, por encima de Suno v5 y MiniMax 2.0. Es más lento y está pensado para canciones con letra |

Tabla de VRAM oficial de ACE-Step 1.5:

| VRAM | DiT | LM |
|:--|:--|:--|
| ≤ 6 GB | 2B turbo | ninguno (INT8 + offload completo) |
| **6–8 GB** | **2B turbo** | **0.6B (PyTorch)** ← la que usamos |
| 8–16 GB | 2B turbo/sft | 1.7B (vLLM) |
| ≥ 24 GB | XL sft | 4B |

## Descartados

| Modelo | Motivo |
|:--|:--|
| ACE-Step 1.5 **XL** (4B) | Pide 12 GB o más con optimizaciones. En 8 GB solo corre con INT8 + offload y la comunidad lo reporta "extremadamente lento" |
| SongGeneration 2 / LeVo 2 (Tencent, mar 2026) | Mínimo 10 GB (16 GB con audio de referencia) |
| YuE / YuE2 | 16 GB en fp16. Cuantizado (exllamav2/mmgp) baja de 8 GB, pero es lento |
| DiffRhythm / DiffRhythm 2 | Sin requisitos claros para 8 GB; pensado para canciones con letra en chino e inglés |
| MusicGen (Meta), Stable Audio Open | **Se descartaron solo por el filtro de idioma, que ya no aplica.** Entran en 8 GB y son buenos para instrumental con prompt en inglés. Son los siguientes candidatos si se quiere comparar |

## Hallazgos de las pruebas

- **ACE-Step** suena a lofi de verdad: batería regular y agudos recortados. El archivo dura lo pedido, pero la música suele terminar antes y el resto es silencio: 0,8 s en 60 s, 0–5 s en 30 s y 10–11 s en 20 s. El script ahora recorta ese silencio.
- **Tonalidad**: cuando no se le pasa, el LM de ACE-Step la elige en cada corrida (D minor en una, G major en otra, con el mismo prompt). Si se le pasa `keyscale`, `bpm` y `timesignature`, los respeta como restricción. Por eso cada preset los define.
- **HeartMuLa** decide solo cuándo terminar. Con un único `[Instrumental]` corta a unos 12 s. Repetir secciones según la duración ayuda, pero no siempre: pidiendo 30 s dio 30 s, y pidiendo 60 s dio 12 s. Su mezcla es más densa y brillante y suena menos lofi.
- **HeartMuLa con torchaudio 2.10** guarda el audio a través de `torchcodec`, que no carga con el CUDA de ese torch (`libnvrtc.so.13`). El script reemplaza `torchaudio.save` por `soundfile`.
## Estilos que soporta ACE-Step (investigación del 2026-10-05)

El **caption** es lo que más pesa en el resultado. Acepta etiquetas separadas por comas, texto libre o ambos, y está entrenado para tolerar los dos formatos. Las dimensiones que documenta la guía oficial son género/estilo, emoción y atmósfera, instrumentos, timbre, estilo de producción y progresión.

Géneros que la documentación y las guías de prompts mencionan como efectivos:

| Familia | Géneros |
|:--|:--|
| Electrónica | techno, progressive house, trance, drum and bass, breakcore, darkwave, synthwave |
| Hip-hop | trap, boom bap, drill, phonk, lo-fi hip-hop, cloud rap, uk drill |
| Rock | indie rock, post-rock, shoegaze, dream pop, post-punk, grunge, doom metal |
| Pop | synth-pop, city pop, k-pop, j-pop, indie pop, hyperpop |
| Jazz | bebop, fusion, smooth jazz, gypsy jazz, cool jazz |
| Orquestal | cinematic, trailer music, orchestral score, baroque, minimalist |
| Acústico | indie folk, bluegrass, bossa nova, americana, sea shanty |
| Ambient | dark ambient, drone, new age, generative |

Reglas de prompt que aplican a música instrumental de fondo:

- **Nombra instrumentos, no adjetivos**: "grand piano, upright bass, brushed drums" le da fuentes de sonido concretas.
- **Añade `no vocals`** y usa géneros con connotación instrumental. Las guías mencionan "underscoring", "BGM", "instrumental score", "scoring music" y "video game music", porque en el entrenamiento abundan sus versiones instrumentales.
- **Tempo y tonalidad van aparte** (`bpm`, `keyscale`): si el caption los contradice, el modelo se confunde.
- **Evita estilos que se contradigan** ("classical strings" con "hardcore metal"). Si hace falta mezclar, conviene expresarlo como evolución en el tiempo, o repetir las palabras del elemento que se quiere reforzar.
- **ACE-Step está entrenado sobre todo con canciones con voz**, así que asume que hay voz salvo que se le indique lo contrario. Las guías recomiendan dejar el campo de letra completamente vacío y elegir el idioma "Instrumental / Auto". Este script envía `[Instrumental]` en la letra y `instrumental=True`, y funciona en la mayoría de los casos, pero no en todos (ver abajo).
- Compás: `4/4` es el más fiable; `3/4` y `6/8` suelen funcionar; los complejos (`5/4`, `7/8`) dependen del estilo.

Para el uso que interesa (tutoriales, publicidad, demos), se armaron presets por **uso** y no solo por género: tutorial, explicativo animado, corporativo, anuncio por rubro (moda, comida, salud, fintech, inmobiliario, auto…), demo de producto (SaaS, app, IA, gadget, dashboard), ambient para foco, cinematográfico, acústico, jazz y latino, electrónica y usos concretos. El catálogo está en `estilos.py` y la lista, en el README.

### Resultado de las pruebas de estilos

Se generaron 119 presets nuevos de 30 s con ACE-Step (LM activo) y se midieron con demucs (voz respecto de la mezcla), `ffprobe` (duración tras recortar) y `volumedetect` (volumen medio).

| Resultado | Cantidad |
|:--|:--|
| Presets probados | 119 |
| Pasan (sin voz, ≥20 s, no mudos) | **117** |
| Descartados por voz | 2 |
| Cortos (<20 s) o casi mudos (<−30 dB de media) | 0 |

Duración tras recortar: 20,6–30 s, mediana 26,8 s.

**Descartados**

| Preset | Caption | Motivo |
|:--|:--|:--|
| `cinematico-epico` | epic cinematic, orchestral, taiko drums, strings, brass, powerful | Voz en la pista y en el reintento (−15,0 y −13,0 dB). Probable coro: el género "epic" lo trae en el entrenamiento |
| `documental-historia` | historical documentary, solemn strings, cello, soft timpani | Voz en 3 de 4 muestras (−15,7, −15,7, −12,3 y una limpia a −33,0 dB) |

Pistas que dieron voz una vez y salieron limpias al regenerar (se mantienen): `meditacion` (−17,6 dB), `afrobeat-ligero` (−22,0 dB), `demo-producto` y `anuncio-lanzamiento`. Hay ocho presets que pasan por poco (entre −25 y −32 dB) y se listan en el README.

### Hallazgos del proceso

- **Voz en instrumental**: aun con `[Instrumental]` e `instrumental=True`, aparece voz en una fracción pequeña de pistas: 2 de 36 en la primera tanda de variantes sobre 9 presets, y 6 de los 119 presets nuevos en la primera pasada (4 detectadas por `--evaluar` y 2 al medir después las 28 que no se evaluaron por el cuelgue). Sube en estilos corales u orquestales ("epic", "documental", "meditación"). Por eso `--evaluar --reintentos` es necesario y no opcional.
- **Whisper no sirve para esto**: alucina frases ("Outro Music", "Let me know what you think about this video…") sobre música instrumental. Demucs mide la voz de verdad: instrumental entre −35 y −44 dB respecto de la mezcla, cantada a propósito −4,9 dB.
- **La generación se puede colgar**: una corrida de 119 pistas se detuvo en la 29 (GPU al 0 % y proceso girando en CPU en el decodificador VAE) y nadie lo notó durante ~50 min. No se reprodujo al relanzar en lotes de 15, así que no se sabe la causa. Conviene lanzar corridas largas en lotes con límite de tiempo.
- **Limitaciones**: una sola muestra por preset, y nadie escuchó las pistas. Las métricas no miden si el estilo se reconoce ni si suena bien.

## Fuentes

- [ACE-Step 1.5 (GitHub)](https://github.com/ACE-Step/ACE-Step-1.5) · [NYU Shanghai RITS](https://rits.shanghai.nyu.edu/ai/ace-step-1-5-open-source-music-generation-that-rivals-commercial-ai/) · [Pinokio](https://pinokio.co/posts/01kgjmc52jd76w5s6jx41aj3sr) · [r/LocalLLaMA](https://redlib.ssps.io/r/LocalLLaMA/comments/1kg9jkq/new_sota_music_generation_model)
- [ACE-Step 1.5 XL (HF)](https://huggingface.co/ACE-Step/acestep-v15-xl-base) · [Patreon: XL en 8 GB](https://www.patreon.com/posts/157516177)
- [HeartMuLa paper (arXiv 2601.10547)](https://arxiv.org/pdf/2601.10547) · [heartlib](https://github.com/HeartMuLa/heartlib) · [ComfyUI FL-HeartMuLa](https://github.com/filliptm/ComfyUI_FL-HeartMuLa)
- [SongGeneration 2](https://gaga.art/blog/songgeneration-2/) · [tencent/SongGeneration](https://huggingface.co/tencent/SongGeneration)
- [DiffRhythm 2](https://huggingface.co/spaces/ASLP-lab/DiffRhythm2)
- Estilos y prompts de ACE-Step: [Tutorial oficial](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/Tutorial.md) · [Musician's Guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ace_step_musicians_guide.md) · [deAPI: Prompting Guide](https://deapi.ai/blog/ace-step-1-5-prompting-guide-how-to-write-tags-structure-lyrics-and-generate-better-music) · [Z.Tools: instrumental prompts](https://z.tools/blog/ace-step-instrumental-prompts) · [Ambience AI: ACE-Step prompt guide](https://www.ambienceai.com/tutorials/ace-step-music-prompting-guide)
- Música de fondo para publicidad y explicativos: [Soundverse: AI music for agencies](https://www.soundverse.ai/blog/article/ai-music-for-agencies) · [Music Prompt Pro: commercial background music](https://musicpromptpro.com/topics/commercial-background-music-prompts)
- [Spheron: YuE, ACE-Step, MusicGen, Stable Audio (2026)](https://www.spheron.network/blog/deploy-open-source-ai-music-generation-gpu-cloud-2026/) · [YuE2 local](https://www.mindstudio.ai/blog/yue2-open-music-generation-model) · [Boppy: modelos open source 2026](https://boppy.me/blog/best-open-source-ai-music-models)
