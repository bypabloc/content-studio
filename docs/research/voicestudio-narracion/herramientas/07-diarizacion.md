# Diarización de Hablantes (Speaker Diarization)

> Investigación del 2026-11-15. Cómo identifica VoiceStudio quién habla y cuándo (pyannote 3.1, Sortformer nativo o una heurística por silencios), dónde se usa (doblaje y transcripción) y cómo se activa. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Clon local consultado: commit `80b4594` (2026-11-16).

---

## 1. Qué Es

* Divide un audio en turnos por hablante y asigna un hablante a cada segmento del ASR **(leída, `docs/features/diarization.md`)**.
* No es un motor del registro ASR: lo usan el pipeline de doblaje y `POST /transcribe` en modo `accurate` **(leída, `docs/engines/README.md` §Speech-to-text)**.
* Tres implementaciones:

| Backend | Modelo | Límite | Licencia de pesos | Fuente |
| :--- | :--- | :--- | :--- | :--- |
| **pyannote** (por defecto) | `pyannote/speaker-diarization-3.1` + `pyannote/segmentation-3.0` + embedding `pyannote/wespeaker-voxceleb-resnet34-LM` | sin tope práctico; acepta un número exacto de hablantes | repos con acceso restringido (*gated*) en Hugging Face | `backend/services/diarization_local.py` L22-29, `diarization.md` **(leída)** |
| **Sortformer v1** (audio.cpp, GGUF Q8) | Sortformer v1 | ≤ 4 hablantes, clips ≤ 120 s, no acepta un número exacto | CC-BY-NC-4.0 | `diarization.md` §Native Sortformer, `backend/services/transcript_diarization.py` **(leída)** |
| **Heurística por silencios** (fallback) | ninguno | una pausa > 1.2 s (`SPEAKER_GAP`) cambia de hablante | — | `backend/services/segmentation.py:35`, L728-757 **(leída)** |

* FunASR (SenseVoice) puede diarizar en línea con su modelo de hablantes `cam++` **(leída, `docs/engines/README.md`)**.

---

## 2. Cómo Se Usa

### 2.1 Activación (una sola vez)

Pasos de `docs/features/diarization.md` §License acceptance flow **(leída)**:

1. Crear un token de Hugging Face y guardarlo en **Settings → Credentials**.
2. Con la misma cuenta, aceptar las condiciones en [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) y [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) ("Agree and access repository").
3. Instalar en **Settings → Models → Diarisation** y esperar a que termine.
4. Después funciona offline: los trabajos solo cargan archivos locales, **nunca descargan pesos durante un trabajo**, y no hace falta conservar el token.

Sin estos pasos la descarga devuelve 401/403 y el doblaje sigue con la heurística **(leída)**.

### 2.2 En la UI

* **Doblaje**: campo **Speakers** bajo el archivo (vacío = automático; 1-20). Ponerlo cuando dos personajes terminan como uno **(leída, `docs/dubbing/multi-speaker-guide.md` §1)**. Luego se corrige a mano con **Set speaker…**, **New speaker** y **Split at cursor** (ver [05](05-doblaje-de-video.md) §2.1).
* **Transcriptions**: en modo *accurate*, el interruptor **Identify speakers** (apagado por defecto) etiqueta cada segmento; si el modelo falta o falla, se guarda la transcripción sin etiquetas y con un aviso **(leída, `docs/electron-transcriptions.md`)**.

### 2.3 Por API / CLI

```bash
# Transcripción de archivo con hablantes (solo mode=accurate)
curl -sS http://localhost:3900/transcribe \
  -F audio=@entrevista.wav -F mode=accurate -F diarize=true -F num_speakers=2
# Respuesta: segments[].speaker = "Speaker 1" | "Speaker 2", speakers[], y
# diarization_error = LOAD_FAILED | DIARIZATION_FAILED | DIARIZATION_TIMEOUT si no pudo

# Doblaje: el número de hablantes va como query
curl -N "http://localhost:3900/dub/transcribe-stream/<job_id>?num_speakers=2"
voicestudio dub transcribe <job_id> --query num_speakers=2
```

Fuentes: `backend/api/routers/capture.py:53` (`diarize`, `num_speakers`), `transcript_diarization.py` (`parse_speaker_hint` 1–20), `dub_core.py:1518` y `:2784` **(leída)**.

Variables para despliegues gestionados: `OMNIVOICE_DIARIZATION_BACKEND` y `OMNIVOICE_DIARIZATION_MODEL` mandan sobre la selección de la UI **(leída, `diarization.md`, `backend/services/diarization_runtime.py`)**.

---

## 3. Opciones y Parámetros

| Parámetro | Valores | Efecto | Fuente |
| :--- | :--- | :--- | :--- |
| `num_speakers` | 1–20; fuera de rango = automático | Número exacto para pyannote; la heurística lo usa como tope cíclico; Sortformer lo ignora | `transcript_diarization.py`, `dub_core.py` (`_clamp_num_speakers`) **(leída)** |
| `diarize` (`/transcribe`) | `true` / omitido | Solo actúa con `mode=accurate` | `capture.py` **(leída)** |
| `reanalyze_speakers` (`transcribe-stream`) | bool | Vuelve a analizar los hablantes | `dub_core.py:1518` **(leída; efecto exacto no verificado)** |
| `per_segment_refs` (`transcribe-stream`) | bool, `true` | Corta una referencia de clonación por línea desde las voces separadas | `dub_core.py:1518`, `competitive-analysis.md` idea 4 **(leída)** |
| Etiquetas | `SPEAKER_00` → `Speaker 1` | Normalización de pyannote | `segmentation.py:911` **(leída)** |

Reglas de asignación (`diarization.md` §What diarization buys you) **(leída)**:

* Una línea con palabras de dos hablantes se parte en el cambio de turno.
* Una respuesta de una palabra que es oración propia ("Fine.") se separa; una palabra suelta dentro de una oración se trata como ruido.
* Lo que cae entre turnos toma el hablante del turno más cercano.
* Un hablante con menos de ~3 s de voz limpia usa la voz por defecto, nunca la de otro hablante.
* Una línea que se solapa con otra no recibe referencia propia, para no mezclar dos voces.

---

## 4. Ejemplos

* **Entrevista de dos personas para un reel**: `Speakers=2` → revisar etiquetas → Cast con una voz por hablante → `voice_match=consistent` **(leída, `multi-speaker-guide.md`)**.
* **Video de 5 personajes** (ejemplo de la guía oficial): `Speakers=5`, corregir con **Set speaker…** antes de traducir **(leída)**.
* **Transcripción etiquetada** para un guion de podcast: `/transcribe` con `mode=accurate&diarize=true`; las etiquetas salen en la lista de segmentos y en los exports de la pestaña Transcriptions **(leída, `electron-transcriptions.md`)**.

---

## 5. Tips y Trucos

* **Fijar el número de hablantes** cuando se sabe: es lo que más evita fusiones de turnos **(leída, `multi-speaker-guide.md`)**.
* **Revisar antes de traducir**: corregir un hablante después obliga a regenerar **(leída)**.
* **Sortformer** sirve para clips cortos (≤ 120 s) con hasta 4 hablantes; en una RTX 4090 procesó 60 s en 3.27 s por Vulkan **(leída, `diarization.md`)**. Para material largo, pyannote.
* Un fallo de carga **no implica** un problema de licencia o token: revisar **Settings → Logs → Backend** **(leída)**.
* La heurística por silencios fusiona voces de tono similar y diálogos rápidos; sirve solo para terminar el trabajo **(leída)**.

---

## 6. Problemas Conocidos

| Issue | Qué pasa | Estado |
| :--- | :--- | :--- |
| [#2163](https://github.com/debpalash/VoiceStudio/issues/2163) | pyannote no se instalaba en Windows (v0.5.2) aun con token y acceso: "no model weights were found in the snapshot"; el usuario no sabía que también hace falta `segmentation-3.0` | Cerrado |
| [#3419](https://github.com/debpalash/VoiceStudio/issues/3419) | Turnos de dos hablantes fusionados en uno aunque se fije el número; solo un hablante clonado | Cerrado |
| [#2471](https://github.com/debpalash/VoiceStudio/issues/2471) | Conservar hablantes conocidos al limpiar respuestas cortas | Cerrado |
| [#2891](https://github.com/debpalash/VoiceStudio/issues/2891) | Sortformer nativo con `turns.json` corrupto: ahora muestra un error claro | Cerrado |

**Conflicto**: `diarization.md` dice que las etiquetas `SPEAKER_00:` salen en los SRT/VTT exportados. En el código, `GET /dub/srt/{job_id}` arma cada cue solo con el texto (`_pick_subtitle_text`, `dub_export.py:2045-2060`) sin hablante, y las etiquetas se normalizan a `Speaker N` **(leída)**. Las etiquetas sí aparecen en los exports de texto de la pestaña Transcriptions **(leída, `electron-transcriptions.md`)**.

---

## 7. Qué Dice la Comunidad

* **B**: según [#3419](https://github.com/debpalash/VoiceStudio/issues/3419), la mezcla de hablantes fue la queja de doblaje más frecuente en Discord entre mayo y julio de 2026 **(leída)**.
* **B**: [#2163](https://github.com/debpalash/VoiceStudio/issues/2163) muestra que la activación *gated* de pyannote confunde a los usuarios **(leída)**.
* No se encontraron reseñas independientes de 2025-2026 sobre la diarización de VoiceStudio **no verificado**.

---

## 8. Qué Sirve para social-videos

| Idea | Cómo aplicarla | Prioridad |
| :--- | :--- | :--- |
| **Hoy no hace falta** | La narración es de una sola voz, generada desde un guion: ya se sabe quién habla | — |
| **Videos con dos voces** (diálogo experta/novata, entrevista) | Si el guion ya marca el hablante por bloque, la diarización sobra: los subtítulos pueden llevar el hablante desde el guion | Baja |
| **Re-locutar material grabado con varias personas** | pyannote 3.1 (MIT según su ficha de modelo, *gated*; **no verificado** en esta investigación) vía `whisperx` o `pyannote.audio` directo, fijando `num_speakers`; reglas de VoiceStudio útiles: partir líneas en el cambio de turno y no clonar desde segmentos solapados ni de menos de ~3 s | Baja |
| **Fallback por silencios** | Cambio de hablante con una pausa > 1.2 s: trivial de implementar, pero impreciso | Solo como último recurso |

No copiar código de `segmentation.py` (AGPL): las reglas descritas arriba son ideas reimplementables.
