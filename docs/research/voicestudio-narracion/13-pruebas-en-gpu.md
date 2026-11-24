# Pruebas en GPU

> Investigación del 2026-11-15. Cómo se probaron los cuatro motores de VoiceStudio en la RTX 4060 Laptop (8 GB, WSL2): instalación, banco de casos, métricas, resultados por caso y la lista de audios para juzgar al oído lo que las métricas no miden. Índice en [README.md](README.md). Todo lo de este capítulo es **medido**.

---

## 1. Entorno

| Elemento | Valor |
| :--- | :--- |
| GPU | RTX 4060 Laptop, 8 GB; ~2.5 GB ocupados por el escritorio de Windows (no liberables desde WSL) |
| Driver | CUDA UMD 13.4 (Windows) |
| SO | WSL2, kernel 6.18 |
| Referencia | `narration/voz/prueba/experta.wav`: 11.52 s, 24 kHz mono, 38 palabras (198 ppm), pico −0.2 dBFS, piso −inf. **No es la voz del usuario** |
| Un motor a la vez | Sí; el daemon Laya (Synapse) se detuvo con autorización del usuario y un vigilante lo detuvo cada vez que reapareció |

---

## 2. Instalación Verificada

| Motor | Comando base | Problemas encontrados y arreglo |
| :--- | :--- | :--- |
| OmniVoice | `uv pip install omnivoice soundfile` | `torch 2.15` → **segfault** en `torch.cuda.is_available()`; fijar `torch==2.14.1 torchaudio==2.11.1` |
| VoxCPM2 | `uv pip install voxcpm soundfile` | El mismo segfault; mismo arreglo. Cargar con `load_denoiser=False, optimize=False` |
| IndexTTS 2.5 | `git clone` + `uv sync --python 3.11 --extra webui` + `hf download` | Ninguno (trae torch 2.8 cu128). Sin `nemo_text_processing` el español no se normaliza |
| CosyVoice 3 | `git clone --recursive` + requirements recortados | `openai-whisper==20231117` no compila; `setuptools≥80` sin `pkg_resources`; `wetext` recibe 403 de ModelScope; torchaudio 2.11 pide `torchcodec`. Arreglos en [06](06-cosyvoice-3.md) §2 |

---

## 3. Banco de Pruebas

* Script `tmp/research-vs/banco.py` (fuera del repo): carga un motor, genera cada caso con las semillas 1 y 2, guarda `wav` + `meta.json` (duración, tiempo, RTF, VRAM pico).
* Script `tmp/research-vs/analizar.py`: whisper `medium` con palabras y tiempos, WER contra el texto (sin tildes ni signos), palabras por segundo, pausas > 0.15 s, F0 con `librosa.pyin` (mediana, rango p10–p90 en semitonos, movimiento final de la última palabra) y F0 penúltimo→último en la enumeración.
* Salidas: `out/narration/research-voicestudio/<motor>/` con `analisis.md` (fuera del repo).

### 3.1 Casos Comunes

| id | Texto | Qué mide |
| :--- | :--- | :--- |
| `c_base` | Mira, el problema real no es la agenda, es la información dispersa. | Línea base |
| `c_homografos` | Hoy termino el informe. Ayer terminó la reunión. Ese término es técnico. | Tilde y sílaba tónica |
| `c_numeros_digitos` / `_letras` | Atendimos 25 pacientes y la consulta cuesta 1500 pesos. (y en letras) | Normalización de números |
| `c_siglas` | Descarga el PDF con el código QR y revisa el IMC. | Siglas sin deletrear |
| `c_pregunta` | ¿Ya revisaste la agenda de mañana? | Subida final |
| `c_exclamacion` | ¡Lo logramos, por fin está listo! | Energía |
| `c_enumeracion_y` | Tienes agenda, recetas, pagos y reportes. | Curva de enumeración |
| `c_pausas` | Primero, abre el editor… luego, sin prisa, revisa el texto — y guarda. | `…` y `—` |
| `c_mayus` / `c_minus` | Esto es MUY importante para tu clínica. (y en minúscula) | Mayúsculas como énfasis |
| `c_ingles` | Abre WhatsApp, entra a Zoom y revisa el stock. | Extranjerismos |
| `c_drama` | La puerta se abrió despacio… y no había nadie. Nadie. | Storytelling |
| `c_anuncio` | ¡Este mes, todos los planes a mitad de precio! No te lo pierdas. | Publicidad |
| `c_tutorial` | En este video te muestro cómo crear tu primera cita en menos de un minuto. | Tutorial |

Más casos por motor: etiquetas (`[laughter]`, `[sigh]`, `[breath]`, `<strong>`, `[pause]`), instrucciones de emoción en español e inglés, vector de emoción, velocidad y modos de clonación.

---

## 4. Resultados por Caso Común

"✓" = whisper transcribió exacto en las 2 semillas; "½" = 1 de 2; "✗" = 0 de 2. En números, ✓ = leído correctamente aunque whisper lo escriba en dígitos.

| Caso | OmniVoice | VoxCPM2 | IndexTTS 2.5 | CosyVoice 3 |
| :--- | :--- | :--- | :--- | :--- |
| Base, tutorial, anuncio, pregunta, exclamación | ✓ | ✓ | ✓ | ✓ |
| Homógrafo "Hoy termino" | ½ (oyó "terminó") | ✗ ("terminó") | ✗ ("terminó") | ½; en otra semilla "terminó" → "termino" |
| Números en dígitos | ✓ | ✓ | **✗** ("mil cimientos", "500") | ✓ |
| Números en letras | ✓ | ✓ | ✓ | ✓ |
| Siglas QR, IMC | **✗** ("query", "IMSS") | ✓ | ✓ | ✓ |
| Enumeración | ½ | ✓ | ✓ | ✓ |
| `…` y `—` (`c_pausas`) | ½ (omitió "el texto") | ✓ | **✗ (lee "—" como "menos")** | ✓ |
| Mayúsculas | Sin efecto | Sin efecto | **Idéntico** (todo se pasa a mayúsculas) | Algo más lento |
| Extranjerismos | ✓ | ½ ("Apera el WhatsApp") | ✓ | ✓ |
| **Drama con `…`** | **✗ (omite "y no había nadie")** | ✓ | ✓ | ✓ |
| Palabras/s (referencia 3.3) | 3.09 | 3.19 | **2.02** | 2.87 |
| VRAM pico | 2.22 GiB | 5.75 GiB | 5.69 GiB | 3.50 GiB |
| RTF mediano | 1.23 | 1.81 | 1.97 | 1.20 |

### 4.1 Etiquetas

| Etiqueta | OmniVoice | VoxCPM2 | IndexTTS 2.5 | CosyVoice 3 |
| :--- | :--- | :--- | :--- | :--- |
| `[laughter]` | No se lee | No se lee | **Se lee** ("Lotter") | No se lee |
| `[sigh]` | No se lee | Altera el inicio | **Se lee** ("SAI") | No se lee |
| `[breath]` | **Se lee** | Altera "Corrí" | **Se lee** | No se lee |
| `<strong>` | **Rompe la salida** | **Se lee** | **Se lee** | No se lee |
| `[pause]` | **Rompe la salida** | No se lee | **Se lee** | **Se lee** ("pausa") |

### 4.2 Emoción

| Motor | Mecanismo | Efecto medido |
| :--- | :--- | :--- |
| VoxCPM2 | `(instrucción)texto` | No se lee en modo controlable; **se lee en Hi-Fi**. En español la duración quedó igual a la base en 7 de 10; en inglés en 3 de 10 |
| IndexTTS 2.5 | Vector de 8 emociones | Cambios coherentes: tristeza 1.5× más lenta; miedo más rápido y agudo; enojo +45 Hz de F0 (perdió el "No" inicial) |
| IndexTTS 2.5 | `emo_text` | Español = inglés en alegre y triste (audio idéntico); +1.1 GiB y RTF ~10 |
| CosyVoice 3 | `instruct2` en inglés | Triste: 5.2–5.8 s (vs 3.5–3.8) y F0 más plana; urgente: hasta 4.2 palabras/s |
| CosyVoice 3 | `instruct2` en español | Leída en voz alta 1 de 10 veces |
| OmniVoice | `instruct` de diseño | `whisper` produce susurro real (sin sonoridad) pero sin clonar la voz |

### 4.3 Velocidad

| Motor | Parámetro | 0.9 / 0.85 | 1.15 |
| :--- | :--- | :--- | :--- |
| OmniVoice | `speed` | +11 % | −12 % |
| CosyVoice 3 | `speed` | +11 % | −13 % |
| IndexTTS 2.5 | `duration_factor` (0.85 / 1.15, inverso) | −15 % | +14 % |

---

## 5. Limitaciones del Banco

* **Una sola referencia** y no es la voz del usuario: el acento, la similitud y la emoción con su voz real quedan pendientes.
* **Dos semillas por caso**: alcanza para detectar fallos sistemáticos (omisiones, etiquetas leídas), no para estimar tasas.
* **Whisper** normaliza tildes y números y tiene su propio sesgo ("Hoy terminó"): los homógrafos se confirman escuchando.
* **F0 con pyin** en frases cortas es ruidoso; el movimiento final es indicativo.
* No se midió similitud de hablante con un modelo de verificación.

---

## 6. Para Escuchar

Las métricas no dicen si una emoción "suena" ni si la risa es convincente. Rutas en `out/narration/research-voicestudio/` (semilla 1):

| Qué juzgar | Archivos |
| :--- | :--- |
| Calidad general por motor (misma frase) | `omnivoice/c_tutorial__s1.wav`, `voxcpm/c_tutorial__s1.wav`, `indextts/c_tutorial__s1.wav`, `cosyvoice/c_tutorial__s1.wav` |
| Drama | `*/c_drama__s1.wav` (OmniVoice omite la mitad) |
| Risa, suspiro, respiración | `omnivoice/t_risa__s1.wav`, `omnivoice/t_suspiro__s1.wav`, `cosyvoice/t_risa__s1.wav`, `cosyvoice/t_respiro__s1.wav`, `cosyvoice/t_enfasis__s1.wav` |
| Emoción VoxCPM2 (inglés vs español) | `voxcpm/v_emo_base__s1.wav`, `voxcpm/v_emo_triste_en__s1.wav`, `voxcpm/v_emo_triste_es__s1.wav`, `voxcpm/v_emo_susurro_en__s1.wav` |
| Emoción IndexTTS (vector) | `indextts/i_emo_base__s1.wav`, `indextts/i_vec_triste_a0.6__s1.wav`, `indextts/i_vec_miedo_a0.6__s1.wav`, `indextts/i_vec_enojado_a0.6__s1.wav` |
| Emoción CosyVoice (instrucción) | `cosyvoice/k_emo_base__s1.wav`, `cosyvoice/k_instr_triste_en__s1.wav`, `cosyvoice/k_instr_urgente_en__s1.wav` |
| Homógrafo "Hoy termino" | `*/c_homografos__s1.wav` |
| Susurro por diseño (OmniVoice) | `omnivoice/o_design_whisper__s1.wav` |
| VoiceStudio vs réplica | `replica/vs/broadcast/c_base__s1.wav`, `replica/local/broadcast/c_base__s1.wav` ([14](14-replicacion-de-voicestudio.md)) |
