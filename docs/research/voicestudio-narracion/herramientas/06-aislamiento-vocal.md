# Aislamiento Vocal (Vocal Isolation)

> Investigación del 2026-11-15. Qué modelo usa VoiceStudio para separar la voz del fondo, en qué partes de la app aparece (limpiar una grabación de referencia, doblaje, cambio de voz en video) y cómo se invoca. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Clon local consultado: commit `80b4594` (2026-11-16).

---

## 1. Qué Es

* No es una herramienta independiente en la UI: es **Demucs `htdemucs` en modo de dos stems** (`vocals` / `no_vocals`), ejecutado como subproceso `python -m demucs.separate --two-stems vocals -n htdemucs -d <device>` **(leída, `backend/api/routers/system.py` ~L1478, `backend/services/dub_pipeline.py:1604`)**.
* Dependencia del proyecto: `demucs>=4.0.1` en `pyproject.toml:99` **(leída)**.
* "Vocal Isolation" figura en el catálogo de funciones (`docs/feature-catalog.md`, `docs/features.yaml`) **(leída)**, pero no tiene página de documentación propia.
* Su análisis competitivo lo califica "A– (Demucs 4-stem)" y reconoce que los modelos ONNX de UVR/Spleeter de otras apps son más livianos **(leída, `docs/competitive-analysis.md` L89)**. **Conflicto** menor: el código siempre usa `--two-stems vocals`, no 4 stems.

Se usa en tres lugares:

| Uso | Para qué | Fuente |
| :--- | :--- | :--- |
| **Limpiar una grabación de micrófono** (referencia para clonar) | Quita ruido y fondo antes de clonar | `POST /clean-audio`, `system.py:1446`; `electron/src/renderer/src/hooks/use-recording.ts` **(leída)** |
| **Doblaje** | Separar la voz para el ASR, cortar referencias de clonación por hablante y conservar música y ambiente en la mezcla final | `dub_pipeline.py` `_separate_background` **(leída)** |
| **Video voice swap** (Tools → Convert) | Convertir solo la voz y volver a mezclar el fondo a su nivel original | `backend/services/video_voice_swap.py` **(leída)** |

---

## 2. Cómo Se Usa

### 2.1 En la UI

* **Clonación por micrófono**: al detener una grabación la app la envía a `/clean-audio`; si falla, carga la grabación cruda y avisa con "loaded raw". No hay botón aparte para elegir **(leída, `use-recording.ts`: "Falls back to the raw recording when `/clean-audio` is unavailable so a missing denoiser never blocks cloning")**.
* **Doblaje**: automático al importar un video; la etapa aparece como `demucs_start` / `demucs_progress` / `demucs_retry` / `demucs_done` en el progreso **(leída, `dub_pipeline.py` ~L1904-1939)**.
* **Video voice swap**: soltar un MP4/MOV/M4V/MKV en Tools → Convert; si Demucs no está instalado se convierte toda la pista y el resultado lo indica **(leída, `docs/electron-tools.md`)**.

### 2.2 Por API / CLI

```bash
# API: devuelve un WAV mono de 24 kHz con la voz aislada
curl -sS -X POST http://localhost:3900/clean-audio \
  -F audio=@grabacion.webm -o limpio.wav -D -
# Cabeceras: X-Clean-Filename: mic_<id>.wav
#            X-Clean-Conversion: fallback  (solo si falló la conversión final con ffmpeg)

# CLI equivalente (cli/voicestudio_cli/registry.py:283)
voicestudio audio clean grabacion.webm   # el archivo va como argumento posicional (cli/voicestudio_cli/__main__.py:147)
```

Comportamiento de `/clean-audio` según `system.py` L1446-1514 **(leída)**:

1. Convierte la subida a WAV 24 kHz mono con ffmpeg (si falla, usa la original).
2. Corre Demucs `htdemucs` con `--two-stems vocals` en el mejor dispositivo, con timeout de 900 s.
3. Si Demucs falla o se pasa del tiempo, **devuelve el audio sin separar** y solo lo registra en el log (no hay error para el cliente).
4. Re-codifica a 24 kHz mono y lo sirve como `audio/wav`.

No existe herramienta MCP para esto **(leída, `backend/mcp_server.py`)**.

---

## 3. Opciones y Parámetros

| Parámetro | Valor | Dónde | Fuente |
| :--- | :--- | :--- | :--- |
| Modelo | `htdemucs` | fijo | `system.py`, `dub_pipeline.py` **(leída)** |
| Stems | `--two-stems vocals` → `vocals.wav` + `no_vocals.wav` | fijo | idem |
| Dispositivo | `get_best_device()` (CUDA/MPS/CPU) | automático | idem |
| Escalera de reintentos (doblaje) | estándar → *lean* `--segment 4 --overlap 0.1` en el mismo dispositivo → *lean* en CPU | `_DEMUCS_LEAN_FLAGS` | `dub_pipeline.py:1547-1605` **(leída)** |
| Timeouts (doblaje) | 1800 s por intento, presupuesto total 3600 s, no reintenta si quedan < 120 s ni tras un timeout | constantes | idem **(leída)** |
| Timeout (`/clean-audio`) | 900 s | constante | `system.py` **(leída)** |
| Formato de salida (`/clean-audio`) | WAV mono 24 kHz | fijo | idem |
| `bed_level` (export del doblaje) | 0.0–4.0, por defecto 1.0, con limitador | query | `docs/dubbing/export.md` **(leída)** |
| Límites del video swap | video ≤ 4 GB, pista ≤ 10 min, comprobado antes de separar | fijo | `electron-tools.md` **(leída)** |

---

## 4. Ejemplos

* **Limpiar una referencia de voz grabada en casa** (ventilador, eco leve): `POST /clean-audio` → WAV 24 kHz mono listo para clonar **(leída)**. Demucs separa voz de *música y fondo*; no es un reductor de ruido de banda ancha ni un de-reverb, así que con un zumbido constante o reverberación el resultado no está garantizado **no verificado**.
* **Separar la música de un video ajeno para doblarlo**: la ingesta del doblaje deja `vocals` y `no_vocals` en la carpeta del trabajo; la exportación con `preserve_bg=1` mezcla el fondo bajo la voz nueva **(leída, `dub_pipeline.py`, `export.md`)**.
* **Stems para editar fuera**: `GET /dub/export-stems/{job_id}` devuelve un ZIP por idioma **(leída, `dub_export.py:2513`)**.

---

## 5. Tips y Trucos

* **Separar desde audio a calidad completa, no desde el de 16 kHz del ASR**: VoiceStudio lo cambió porque el fondo quedaba mono y "apagado"; Demucs re-muestrea a 44.1 kHz internamente de todos modos **(leída, comentario en `dub_pipeline.py` ~L1772-1780)**.
* **Si la separación falla, no reutilizar la mezcla como "voces"**: un reintento debe volver a separar (`background_separation == "failed"` fuerza otra pasada) **(leída, `dub_pipeline.py` ~L377-391)**.
* **Alinear inicios de línea solo sobre la voz separada**: sobre la mezcla, el ajuste por energía se desactiva porque un suspiro o un paso movía el inicio (#963, #3419) **(leída, `dub_core.py` ~L1746, L2444)**.
* **Fuentes largas**: usar `--segment 4 --overlap 0.1` para bajar la memoria antes de caer a CPU **(leída)**.
* La separación puede afectar sonidos que se solapan con el diálogo; el aislamiento exacto desde una mezcla no está garantizado **(leída, `electron-dubbing.md`)**.

---

## 6. Problemas Conocidos

| Issue | Qué pasa | Estado |
| :--- | :--- | :--- |
| [#3751](https://github.com/debpalash/VoiceStudio/issues/3751) | Demucs termina con código 1 al 99 % en una fuente de ~1 h (Windows, CUDA, v0.5.7); la exportación con fondo falla | Cerrado; motivó la escalera de reintentos |
| [#3750](https://github.com/debpalash/VoiceStudio/issues/3750) | Pedido de cambiar la voz de un video conservando la entrega y el fondo | Cerrado; implementado como Video voice swap |
| [#1669](https://github.com/debpalash/VoiceStudio/issues/1669) | Backend muerto (`-1073741819`) en Windows; aparece en la búsqueda de "demucs" | Cerrado; relación con Demucs **no verificada** |

* **Licencia**: `backend/config/model_licenses.json` registra `htdemucs` con `license: NOASSERTION`, `commercial_use: false`, `review_status: unreviewed` **(leída)**. El código de Demucs es MIT, pero la licencia de los pesos no está revisada por el propio proyecto: verificarla antes de usarlo comercialmente **no verificado**.

---

## 7. Qué Dice la Comunidad

* **B**: [#3751](https://github.com/debpalash/VoiceStudio/issues/3751) muestra a un usuario que no pudo exportar con fondo por un fallo de Demucs en una fuente larga **(leída)**.
* **C**: `docs/competitive-analysis.md` del propio repo compara con voice-pro y pyvideotrans (Demucs/UVR) y reconoce que los modelos ONNX de la competencia son más livianos **(leída)**.
* No se encontraron opiniones independientes de 2025-2026 sobre la calidad de su aislamiento **no verificado**.

---

## 8. Qué Sirve para social-videos

| Idea | Cómo aplicarla | Prioridad |
| :--- | :--- | :--- |
| **Paso opcional de limpieza de referencias** | `demucs --two-stems vocals -n htdemucs` sobre la grabación antes de clonar, y luego la validación con ffmpeg de [11](../11-audio-de-referencia.md) §7. Llamar a Demucs como herramienta externa (MIT), sin copiar el código AGPL | Media: lo ideal sigue siendo grabar limpio |
| **Fallback silencioso pero visible** | Si la limpieza falla, seguir con el original y **decirlo** en la salida (VoiceStudio solo lo registra en el log en `/clean-audio`) | Media |
| **Doblar videos con música** | Separar `no_vocals` y mezclarlo bajo la narración traducida; útil para re-locutar un video propio ya publicado | Baja-media |
| **No separar desde 16 kHz** | Si se separa, hacerlo desde el audio original a 44.1/48 kHz | Regla |
| **VRAM** | Demucs corre en GPU: respetar "un modelo a la vez" (no junto al TTS en 8 GB) | Regla |

No hace falta para la música de `music/`: es instrumental generada y no lleva voz que quitar.
