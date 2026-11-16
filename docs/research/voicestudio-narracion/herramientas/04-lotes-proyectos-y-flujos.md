# Lotes, Proyectos y Flujos

> Investigación del 2026-11-15. Cubre **Batch Queue** (doblaje por lotes y watch folders), **Projects** (biblioteca), **Workflows** (pipelines sobre muchos guiones), **Gallery** y **Playback**. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

| Herramienta | Qué hace | Fuente |
| :--- | :--- | :--- |
| Batch Queue | Cola de **doblaje de videos**: transcribe, traduce, sintetiza y mezcla por idioma. **No** es una cola de TTS para guiones | `docs/electron-batch.md`, `backend/api/routers/batch.py:815` **(leída)** |
| Watch folder | Vigila una carpeta y encola automáticamente los videos nuevos con los últimos ajustes usados | `CHANGELOG.md` (#1768), `electron/src/main/watch-folders.ts` **(leída)** |
| Projects | Biblioteca unificada: proyectos de doblaje, Stories, Audiobooks, voces, transcripciones, takes, exportaciones y renders | `docs/electron-projects.md` **(leída)** |
| Workflows | Lienzo de pasos que procesa en serie hasta 50 entradas (guiones o clips) | `docs/electron-workflows.md` **(leída)** |
| Gallery | Catálogo de arquetipos, voces de Community y My Imports | `docs/electron-gallery.md` **(leída)** |
| Playback | Reproductor Vidstack compartido (forma de onda con WaveSurfer) | `docs/electron-playback.md` **(leída)** |

**Conflicto** de expectativa: material de marketing como `deploy/dockerhub-overview.md` ("drop 50 videos and walk away") presenta Batch Queue como algo genérico, pero en el código es solo de doblaje. Para **TTS por lotes** lo que corresponde es **Workflows** (plantilla "Read scripts aloud in one voice, one clip per script"). **(leída)** i18n `workflows.template_recipe`.

---

## 2. Cómo Se Usa

### 2.1 Batch Queue (UI)

1. Abrir **Batch dubbing**. Añadir videos (selector o arrastrar), uno o varios idiomas destino, una voz guardada opcional y la opción de preservar el fondo. **Add to Queue**. **(leída)** `docs/electron-batch.md`.
2. Las vistas Active, Completed y Failed consultan los trabajos. Los activos se pueden cancelar; borrar los terminados pide confirmación. **(leída)**
3. **Watch folder**: elegir un directorio. Los archivos nuevos que terminan de copiarse se suben y se encolan solos, con controles Pause, Resume y Stop. Requiere la app de escritorio o un navegador Chromium. **(leída)** i18n `batch.watch_*`.

API (`batch.py:815`):

```bash
curl -X POST http://127.0.0.1:3900/batch/enqueue \
  -F video=@reel.mp4 -F langs=en,pt -F voice_id=<profile_id> -F preserve_bg=true
voicestudio batch list --status active
voicestudio batch download <job_id> en
```

El servidor rechaza los archivos que no son media (415), un perfil inválido (422) y la falta de modelo ASR (409, sin descarga silenciosa). **(leída)**

### 2.2 Workflows (UI)

1. Ir a `#/workflows` → **New** o **New from template**. Plantillas de narración: leer guiones con una voz; leer y normalizar; transcribir; convertir voz; localizar (transcribir → traducir → narrar). **(leída)** i18n `workflows.template_*`.
2. Paso de entrada **Start** (guiones, uno por cada separador `---` o archivos importados) o **Audio** (clips). Límites: 50 ítems, 20.000 caracteres por guion y 64 MiB por clip. **(leída)** `docs/electron-workflows.md`.
3. Pasos ejecutables: Speak, Convert, Transcribe, Translate (Argos o NLLB), Normalize (pico objetivo de -24 a -1 dB, -2 por defecto), Condition y End. **Agent** y **Call** son borradores que no corren. **(leída)** ídem, `features/workflows/workflow-model.ts`, `workflow-inputs.tsx:89`.
4. **Condition**: Contains, Is exactly, Starts with o Ends with (ignora mayúsculas y espacios) → ramas `yes` y `no`, por ejemplo con otra voz en cada una. **(leída)**
5. **Run**: ejecución en serie con checkpoint por paso. Stop conserva lo hecho y Run reanuda. Un fallo detiene la corrida para reintentar. **(leída)**
6. Cada ítem terminado se guarda a mano: `.wav` para audio y `.txt` para texto. Nada se descarga automáticamente. **(leída)**

No encontré una API REST ni un comando CLI de Workflows: los borradores viven en el almacenamiento del navegador. **(leída)** `docs/electron-workflows.md`.

### 2.3 Projects

- **All projects** lista Dubbing, Stories y Audiobooks. Voces, transcripciones, takes y exportaciones van bajo **Library**. Hay búsqueda, vista lista/cuadrícula, renombrado inline y borrado múltiple con revisión. **(leída)** `docs/electron-projects.md`.
- Borrar un proyecto elimina el registro, pero **no** los medios fuente ni los generados. Borrar voces o takes sí borra su audio. **(leída)**
- Cada render terminado muestra una receta (voz · velocidad · motor · duración) y el panel **How it was made**. **(leída)** `docs/electron-longform.md`.
- API: `/projects` (solo doblaje), `DELETE /export/history/{id}`, `DELETE /longform/jobs/{job_id}`. CLI: `voicestudio projects list|show|create|update|export|import`. **(leída)**

### 2.4 Gallery

- **Archetypes**: filtros de edad, género, tono, acento, idioma y susurro; favoritos; **Use voice** → perfil de diseño + Design. **(leída)** `docs/electron-gallery.md`.
- **Community**: filtros por pack e idioma, insignia "New" para lo añadido en los últimos 30 días; **Open in Design**. **(leída)**
- CLI: `voicestudio gallery presets list --lang es --gender female`, `gallery presets use <id> --name ...`, `gallery community list --lang es`. **(leída)** `cli/voicestudio_cli/contracts.json`.

### 2.5 Playback

Un solo reproductor activo: abrir otro pausa el anterior. Para audio largo hay barra de búsqueda en lugar de forma de onda. Si la reproducción falla, Download sigue disponible. **(leída)** `docs/electron-playback.md`.

---

## 3. Opciones y Parámetros

| Herramienta | Parámetro | Valores | Fuente |
| :--- | :--- | :--- | :--- |
| Batch | `langs` | Códigos separados por coma (por defecto `es`) | `batch.py` **(leída)** |
| Batch | `voice_id` | Perfil guardado; se re-resuelve en el worker | ídem **(leída)** |
| Batch | `preserve_bg` | true (por defecto) | ídem **(leída)** |
| Batch | `translation_provider` | Opcional | ídem **(leída)** |
| Batch | Persistencia | La cola vive **en memoria**: si el backend se reinicia, se pierde | `docs/electron-batch.md` **(leída)** |
| Workflows | Ítems por corrida | ≤ 50 | `docs/electron-workflows.md` **(leída)** |
| Workflows | Guion | ≤ 20.000 caracteres; separador `---` | ídem **(leída)** |
| Workflows | Speak | voz, idioma, velocidad | `workflow-model.ts` **(leída)** |
| Workflows | Normalize | `targetDb` de -24 a -1 (por defecto -2), pico | `workflow-inputs.tsx:89` **(leída)** |
| Workflows | Condition | contains, equals, starts, ends | `workflow-model.ts:30` **(leída)** |

---

## 4. Ejemplos

**Workflow "5 reels, una voz, normalizados"**: Start con guiones separados por `---` → Speak (voz "Narrador ES", Spanish, 1,05×) → Normalize (-2 dB) → End.

```text
Tip 1: duplica capas con Alt. [pause 0.3s] Ahorra minutos.
---
Tip 2: usa marcadores con la tecla M.
---
Tip 3: exporta en H264 para redes.
```

**Workflow con rama por idioma**: Start → Condition ("Starts with" `EN:`) → `yes`: Speak con voz inglesa → End; `no`: Speak con voz en español → End. Las dos ramas terminan en audio, así que el tipo es compatible si se vuelven a unir. **(leída)** reglas de `docs/electron-workflows.md`.

**Localizar un tutorial grabado**: Audio (clip) → Transcribe → Translate (es → en, NLLB) → Speak (voz clonada) → Normalize → End.

**Watch folder para doblar reels**: apuntar a `~/Reels/salida`; cada MP4 exportado se dobla a `en` con la voz guardada y el fondo preservado.

---

## 5. Tips y Trucos

- Para TTS por lotes, usar Workflows y no Batch Queue (que es de doblaje). **(leída)**
- Los Workflows corren en serie para evitar cargas de modelo simultáneas. Encaja con la regla "un modelo a la vez en la GPU". **(leída)**
- El progreso guardado depende de los ajustes ejecutables: cambiar una voz o una conexión invalida la corrida; mover un nodo o renombrar un paso no. **(leída)**
- El watch folder sube bytes, no rutas, y espera a que el archivo termine de copiarse antes de encolarlo. **(leída)** CHANGELOG #1768.
- Batch Queue no sobrevive a un reinicio del backend. Conviene no encolar trabajos largos antes de actualizar la app. **(leída)**
- Exportar un proyecto como bundle exige incluir el medio fuente; el importador no descarga URL remotas. **(leída)** `docs/electron-projects.md`.

---

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#4065](https://github.com/debpalash/VoiceStudio/issues/4065) | Cerrado | No había cola de takes en Voice Cloning; se pidió encolar generaciones **(leída)** |
| [#3419](https://github.com/debpalash/VoiceStudio/issues/3419) | Cerrado | En doblaje multihablante los turnos se fusionaban, solo un hablante recibía clon y el tiempo se desfasaba **(snippet)** |
| [#3821](https://github.com/debpalash/VoiceStudio/issues/3821) | Cerrado | El doblaje convertía etiquetas de idioma no listadas en otro idioma ("estonian becomes Spanish") **(snippet)** |
| [#4089](https://github.com/debpalash/VoiceStudio/issues/4089) | Cerrado | El doblaje descartaba la referencia de los perfiles que tenían instrucciones de estilo **(snippet)** |
| — | Doc | No hay ninguna prueba que establezca un batch completo con modelos reales ni una transferencia a una máquina remota separada **(leída)** `docs/electron-batch.md` |

---

## 7. Qué Dice la Comunidad

- **B**: [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) valora que los motores sin clonación se rechacen en batch en vez de cambiarse en silencio ("failing loudly"). Recomienda seguir las releases y no `main` (beta), y revisar la licencia del motor antes de un uso comercial del lote. **(leída)**
- **C**: [computingforgeeks](https://computingforgeeks.com/install-voicestudio/) y los listados describen Batch Queue con per-job progress, sin pruebas. **(snippet)**
- No encontré a nadie de la comunidad que hable de Workflows. Es una función reciente. **No verificado**.

---

## 8. Qué Sirve para social-videos

1. **Modo lote en `tts.py`**: un archivo con guiones separados por `---` → un WAV por guion, en serie, con un modelo cargado una sola vez.
2. **Checkpoint por ítem**: si existe la salida con el mismo hash de entrada y ajustes, se salta. Stop y reanudación sin regenerar, e invalidación si cambian la voz o los parámetros.
3. **Normalización final por pico** (-2 dBFS) o por loudness como paso opcional (`--normalizar`).
4. **Enrutado simple por prefijo** (`EN:` / `ES:`) para elegir la voz por ítem, sin un motor de workflows.
5. **Receta "How it was made"**: escribir junto a cada salida un JSON con voz, motor, semilla, velocidad y duración (sin el texto del guion si es sensible) para reproducir takes.
6. **Watch folder**: no hace falta. Un `inotifywait` sobre una carpeta de guiones que llame al CLI cubre el caso si se necesita.
7. No copiar Batch Queue: el doblaje de video está fuera del alcance de `narration/`.
