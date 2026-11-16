# Aplicación a social-videos

> Investigación del 2026-11-15. Cómo llevar lo investigado a `narration/tts.py`: qué motores sumar, con qué parámetros, qué piezas de VoiceStudio reimplementar y qué riesgos quedan. Es una **propuesta**: la implementación espera las [preguntas abiertas](README.md#preguntas-abiertas). Índice en [README.md](README.md).

---

## 1. Lo que `tts.py` Ya Tiene

| Pieza | Estado | Equivalente en VoiceStudio |
| :--- | :--- | :--- |
| Un venv por motor, relanzado automáticamente (`usar_venv`) | Hecho | Sidecars por motor |
| Corte por línea en blanco y `[pausa N]`, con silencio real | Hecho | `[pause N]` + `_render_with_pauses` |
| Bloques de ~300 letras cortados en fin de oración | Hecho | `max_chunk_chars=800` + *crossfade* de 50 ms |
| Recorte del silencio de los bordes de cada bloque y gaps fijos (0.25 / 0.6 s) | Hecho | Trim a −40 dBFS + `line_gap_ms` / `paragraph_gap_ms` |
| Aviso si el texto trae `[…]`, `<…>` o `**` | Hecho | Insert menu que solo ofrece etiquetas válidas |
| `--evaluar` con whisper por párrafo y `--reintentos` | Hecho | `Check audio` (solo señal, sin transcripción) |
| Estilos con referencia propia y velocidad (`atempo`) | Hecho | Perfiles de voz |
| Semilla fija por bloque | **No** | Semilla de la toma reiniciada en cada trozo (#3730) |
| Masterización / loudness | **No** | `broadcast`: HPF + nivelador + EQ + limitador + pico −2 dBFS |
| Marca de agua | Solo Chatterbox (PerTh) | AudioSeal en todo audio sintético |
| Metadatos por toma | **No** | Cabeceras `X-Seed`, `X-Gen-Time`, `X-Audio-Duration` |

`tts.py` ya replica la mayor parte del flujo de VoiceStudio para narración. Lo que falta son motores, semilla, masterización y metadatos.

---

## 2. Motores Propuestos

| `--modelo` | Venv | Llamada | Parámetros por defecto | Licencia |
| :--- | :--- | :--- | :--- | :--- |
| `omnivoice` | `.venv-omnivoice` (Python 3.12, `torch==2.14.1`) | `create_voice_clone_prompt` una vez + `generate(language='es', num_step=32)` | `speed` del estilo | **No comercial** |
| `voxcpm2` | `.venv-voxcpm` (Python 3.12, `torch==2.14.1`) | Hi-Fi (`reference_wav_path` + `prompt_wav_path` + `prompt_text`) por defecto; controlable con `--instruccion` | `cfg_value=2.0`, `inference_timesteps=10`, `load_denoiser=False`, `optimize=False`, `retry_badcase_max_times=1`, `max_len` acotado | Apache-2.0 |
| `indextts` | Repo `index-tts` con `uv sync --extra webui` (Python 3.11, torch 2.8) | `infer(lang='es', max_text_tokens_per_segment=60)`; `use_qwen_emo` solo si hay `emo_text` | `emo_vector` normalizado (suma ≤ 0.8), `emo_alpha` ≤ 0.6 | **bilibili (restrictiva)** |
| `cosyvoice3` | Repo `CosyVoice` con requirements recortados (Python 3.10, `torch==2.14.1`) | `inference_zero_shot` con `You are a helpful assistant.<\|endofprompt\|>` + transcripción, `text_frontend=False` | `speed` del estilo | Apache-2.0 (con *disclaimer* académico) |

Las instalaciones de los cuatro están verificadas en esta máquina ([13](13-pruebas-en-gpu.md) §2). Un modelo a la vez en la GPU (regla 2 de `AGENTS.md`); los picos de VRAM medidos están en [07](07-comparativa-y-licencias.md).

### 2.1 Filtrado de Marcas por Motor

`tts.py` debería traducir o quitar las marcas antes de llamar al modelo, porque el modelo las lee o se rompe ([08](08-guion-y-pronunciacion.md) §5):

| Marca en el guion | omnivoice | voxcpm2 | indextts | cosyvoice3 | qwen / chatterbox |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[pausa N]` | Silencio real (ya existe) | Igual | Igual | Igual | Igual |
| `[risa]` | `[laughter]` | `[laughing]` (sin probar) | Quitar | `[laughter]` | Quitar |
| `[suspiro]` | `[sigh]` | Quitar | Quitar | `[sigh]` | Quitar |
| `[respiro]` | Quitar | Quitar | Quitar | `[breath]` | Quitar |
| `[enfasis]…[/enfasis]` | Quitar | Quitar | Quitar | `<strong>…</strong>` | Quitar |
| `—` | Dejar | Dejar | **Reemplazar por `,`** | Dejar | Dejar |
| Dígitos | Dejar | Dejar | **Rechazar o convertir a letras** | Dejar | Letras (regla 13) |

Columnas medidas en [13](13-pruebas-en-gpu.md) §4.1.

---

## 3. Piezas de VoiceStudio para Reimplementar (sin Copiar Código AGPL)

| Pieza | Por qué | Esfuerzo |
| :--- | :--- | :--- |
| **Semilla por bloque** (`--semilla`, por defecto aleatoria y guardada) | Repetir una toma buena; VoiceStudio la reinicia en cada trozo para que la voz no cambie a mitad de la toma | Bajo |
| **Metadatos `.json`** al lado del `.wav` (motor, semilla, referencia, parámetros, duración, tiempo, observaciones de `--evaluar`) | Reproducir y comparar | Bajo |
| **Masterización opcional** (`--master broadcast`): HPF 80 Hz, nivelador lento, EQ suave, limitador −1 dB, pico −2 dBFS; o `loudnorm` a −16 LUFS para redes | Volumen parejo entre párrafos y videos; la réplica de [14](14-replicacion-de-voicestudio.md) muestra que el nivelador cambia el resultado | Medio |
| **Emoción por párrafo** (`[emocion: …]` al inicio de un párrafo): instrucción en VoxCPM2 y CosyVoice, vector o texto en IndexTTS | Una emoción por bloque es la práctica de todos los proveedores | Medio |
| **Referencia por párrafo** (`[estilo: dramatica]`) | La única palanca emocional de Qwen, OmniVoice y Chatterbox | Medio |
| Gramática longform: `[voz:]`, `[lento]`, `[rapido]` | Multivoz en storytelling | Medio |
| Subtítulos SRT/ASS desde las palabras de whisper que `--evaluar` ya calcula | Reels con subtítulos por palabra | Medio |
| Marca de agua AudioSeal (`--marca`) | Publicación responsable; Chatterbox ya marca | Bajo-medio |

---

## 4. Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| OmniVoice e IndexTTS en videos monetizados | Avisar en el README y en la salida del script; no usarlos como modelo por defecto |
| OmniVoice omite tramos tras `…` | `--evaluar` obligatorio con OmniVoice, o reemplazar `…` por `,` a mitad de oración |
| VoxCPM2 lee la instrucción en modo Hi-Fi | No permitir `--instruccion` en modo Hi-Fi |
| Cuatro venvs y dos repos clonados (~25 GB con pesos) | Instalar solo los motores que se usen |
| CosyVoice lee los números en inglés | Exigir números en letras (regla 13) y `text_frontend=False` |
| Acento con la voz real del usuario | Validar con las grabaciones propias antes de elegir motor por defecto |
