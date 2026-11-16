# Herramientas de VoiceStudio, Una por Una

> Investigación del 2026-11-15. Cómo se usa cada herramienta de [VoiceStudio](https://github.com/debpalash/VoiceStudio) por separado, con ejemplos, tips, problemas conocidos y qué conviene copiar en `narration/tts.py`. La fuente principal es el código del repo (clon del commit `80b4594`); la comunidad y los blogs la complementan. Ninguna herramienta se ejecutó en la UI: lo verificado en GPU está en [../13-pruebas-en-gpu.md](../13-pruebas-en-gpu.md) y la réplica de `/generate` en [../14-replicacion-de-voicestudio.md](../14-replicacion-de-voicestudio.md). Índice general en [../README.md](../README.md).

---

## Índice

| # | Herramienta | Qué cubre | Relevancia para narración |
| :--- | :--- | :--- | :--- |
| 01 | [Clonación de voz](01-clonacion-de-voz.md) | Referencia, transcripción, perfiles, bloqueo de identidad, calidad, controles, emoción, pronunciación | **Alta** |
| 02 | [Diseño de voz](02-diseno-de-voz.md) | Taxonomía de OmniVoice, motores de texto libre, de diseño a voz guardada | Media (voces de personaje) |
| 03 | [Audiolibros e historias](03-audiolibros-e-historias.md) | Gramática del guion longform (`[voice:]`, `[emotion:]`, `[slow]`, `[pause]`…), uniones, loudness | **Alta** |
| 04 | [Lotes, proyectos y flujos](04-lotes-proyectos-y-flujos.md) | Batch Queue, Projects, Workflows (narración por lotes con `---`), Gallery | Media |
| 05 | [Doblaje de video](05-doblaje-de-video.md) | Transcribir, traducir, asignar voces, ajustar tiempos, mezclar | Media (videos en inglés) |
| 06 | [Aislamiento vocal](06-aislamiento-vocal.md) | Demucs `htdemucs` de 2 stems | Baja (limpiar referencias, con cuidado) |
| 07 | [Diarización](07-diarizacion.md) | pyannote 3.1, Sortformer, heurística por silencios | Baja (una sola voz) |
| 08 | [Transcripción](08-transcripcion.md) | WhisperX, faster-whisper, Parakeet; SRT, VTT y palabras con tiempos | **Alta** (subtítulos de la narración) |
| 09 | [Dictado](09-dictado.md) | Widget con atajo global y sherpa-onnx | Baja |
| 10 | [API local y CLI](10-api-local-y-cli.md) | `POST /generate`, NDJSON, `/ws/tts`, `/v1/audio/speech`, CLI `voicestudio` | Media (diseño de flags y metadatos) |
| 11 | [MCP y agentes](11-mcp-y-agentes.md) | Servidor MCP, voces por agente, skills | Baja hoy (Claude Code ya corre `tts.py`) |
| 12 | [Integraciones y llamadas](12-integraciones-y-llamadas.md) | n8n, Twilio, agente de llamadas | Baja |
| 13 | [Marca de agua](13-marca-de-agua.md) | AudioSeal invisible, tono audible, logo en video | Media (publicación responsable) |
| 14 | [Modelos y hardware](14-modelos-y-hardware.md) | Catálogo, descargas, GPU, 8 GB de VRAM, GPU remota | **Alta** |
| 15 | [Entrenamiento y fine-tuning](15-entrenamiento-y-fine-tuning.md) | Afinar OmniVoice con la voz propia | Baja (no comercial y no cabe en 8 GB) |
| 16 | [Instalación y privacidad](16-instalacion-y-privacidad.md) | Linux, WSL2, Docker, datos guardados, red | Media (si se usa la app) |

---

## Lo Más Útil para social-videos

1. **Gramática de guion longform** ([03](03-audiolibros-e-historias.md)): precedencia `# capítulo → [voice:] → [emotion:] → [pause] → SSML-lite → [spell]`; `[slow]` = 0.85, `[fast]` = 1.15, `[emphasis]` = 0.92 + énfasis; `[emotion:]` se reinicia en cada `[voice:]`. Se puede reimplementar en `tts.py` sin copiar código.
2. **Uniones explícitas** ([03](03-audiolibros-e-historias.md)): recortar el silencio propio del motor (−40 dBFS, dejar 40 ms) y poner gaps elegidos (~250 ms entre líneas, ~350 ms entre párrafos); `[pause]` reemplaza el gap, no se suma; rellenar con *room tone* evita el corte a cero digital.
3. **Semilla fija por trozo** ([01](01-clonacion-de-voz.md)): si avanza en cada trozo, la voz cambia a mitad de la toma (issue #3730). "Bloquear identidad" = toma ganadora + semilla como nueva referencia.
4. **Subtítulos** ([08](08-transcripcion.md)): palabras con tiempos y re-segmentación propia para formato vertical; karaoke `.ass` por palabra.
5. **Metadatos por toma** ([10](10-api-local-y-cli.md)): semilla, duración, tiempo de generación y trozos perdidos en un `.json` al lado del `.wav`.
6. **Marca de agua** ([13](13-marca-de-agua.md)): AudioSeal (MIT, CPU) después de normalizar. Chatterbox ya marca con PerTh.
7. **No afinar OmniVoice** ([15](15-entrenamiento-y-fine-tuning.md)): un modelo afinado sigue siendo no comercial y el trainer no cabe en 8 GB.
