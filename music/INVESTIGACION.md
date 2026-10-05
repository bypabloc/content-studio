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
## Fuentes

- [ACE-Step 1.5 (GitHub)](https://github.com/ACE-Step/ACE-Step-1.5) · [NYU Shanghai RITS](https://rits.shanghai.nyu.edu/ai/ace-step-1-5-open-source-music-generation-that-rivals-commercial-ai/) · [Pinokio](https://pinokio.co/posts/01kgjmc52jd76w5s6jx41aj3sr) · [r/LocalLLaMA](https://redlib.ssps.io/r/LocalLLaMA/comments/1kg9jkq/new_sota_music_generation_model)
- [ACE-Step 1.5 XL (HF)](https://huggingface.co/ACE-Step/acestep-v15-xl-base) · [Patreon: XL en 8 GB](https://www.patreon.com/posts/157516177)
- [HeartMuLa paper (arXiv 2601.10547)](https://arxiv.org/pdf/2601.10547) · [heartlib](https://github.com/HeartMuLa/heartlib) · [ComfyUI FL-HeartMuLa](https://github.com/filliptm/ComfyUI_FL-HeartMuLa)
- [SongGeneration 2](https://gaga.art/blog/songgeneration-2/) · [tencent/SongGeneration](https://huggingface.co/tencent/SongGeneration)
- [DiffRhythm 2](https://huggingface.co/spaces/ASLP-lab/DiffRhythm2)
- [Spheron: YuE, ACE-Step, MusicGen, Stable Audio (2026)](https://www.spheron.network/blog/deploy-open-source-ai-music-generation-gpu-cloud-2026/) · [YuE2 local](https://www.mindstudio.ai/blog/yue2-open-music-generation-model) · [Boppy: modelos open source 2026](https://boppy.me/blog/best-open-source-ai-music-models)
