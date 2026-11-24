# Lote 034–039: hablantes (diarización con pyannote)

Pedido del usuario (2026-11-24): identificar **quién habla y cuándo**. Hay dos usos:

* como **opción complementaria de la transcripción** («Identificar hablantes»);
* como **herramienta aparte para solo diarizar**.

El motor es pyannote.audio 4.x con `pyannote/speaker-diarization-community-1`, ejecutado después de faster-whisper. Investigación principal: [`docs/research/diarizacion-pyannote/`](../../research/diarizacion-pyannote/README.md).

Formato: [`plan-format.md`](../../../.agents/rules/plan-format.md). Cada spec es una rama desde `origin/dev` y un PR a `dev`, en orden. La 039 hace la verificación integral y borra esta carpeta.

## Specs

| Spec | Qué | Tipo | Escala | Depende de | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [034](034-diarization-engine/README.md) | Motor `pyannote`: receta, familia `diarization`, token de Hugging Face guardado sin exponerse e instalación de un repositorio restringido | feature | Large | — | PEN |
| [035](035-diarize-job/README.md) | Trabajo `diarize`, unión palabra-hablante, `transcribe` con hablantes, exportaciones, audio por hablante, caché y `studio diarize` | feature | Large | 034 | PEN |
| [036](036-transcription-section/README.md) | Sección **Transcripción**: modelo, idioma, «Identificar hablantes», texto por turnos, renombrar y exportar TXT | feature | Large | 035 | PEN |
| [037](037-speakers-section/README.md) | Sección **Hablantes** (solo diarizar): línea de tiempo con colores, exportar turnos, un audio por hablante y abrir en el Editor | feature | Large | 036 | PEN |
| [038](038-speakers-everywhere/README.md) | Hablantes en Subtítulos (etiqueta, color, prefijo), en la pista del Editor y en la revisión del Limpiador | feature | Large | 037 | PEN |
| [039](039-integral-verification/README.md) | Verificación integral con audio real, mediciones de VRAM y calidad, y cierre del lote | chore | Micro | 038 | PEN |

## Decisiones del usuario que valen para todo el lote

* **Dos entradas** (2026-11-24):
  * una sección nueva **Transcripción**, con el interruptor «Identificar hablantes»;
  * una herramienta aparte para solo diarizar, la sección **Hablantes**.

  Subtítulos, el Editor y el Limpiador también ofrecen el interruptor al transcribir.
* **Salida de «solo diarizar»**: línea de tiempo con colores y nombres editables; turnos en JSON, RTTM y CSV; un audio por hablante; «Abrir en el Editor».
* **Dónde se ve el hablante**:
  * Subtítulos: etiqueta y color;
  * texto exportable «Ana: …»;
  * pista de subtítulos del Editor con colores;
  * transcripción de la revisión del Limpiador.
* **Pesos del modelo**: con el **token del usuario**. El usuario acepta las condiciones de community-1 en Hugging Face y pega su token una vez en la tarjeta del motor. La app lo guarda sin mostrarlo y, después de instalar, todo corre sin conexión.

## Requisito del usuario antes de las corridas reales

Las corridas reales de la 035 en adelante necesitan el motor instalado. Para eso, el usuario:

1. acepta las condiciones en https://huggingface.co/pyannote/speaker-diarization-community-1 con su cuenta;
2. crea un token de lectura en https://huggingface.co/settings/tokens;
3. lo pega en Motores > Diarización.

Mientras falte, cada spec deja las pruebas con pytest y e2e en verde, y la corrida real queda en `PENDING/` con la categoría `blocked — user-credential`. Es el único bloqueo previsto del lote.

## Relación con el lote 025–033

Los dos lotes son independientes. Si la 026 (venvs en la Python más alta) se fusiona antes que la 034, la 034 abre con una fase `0-ajustes` que lleva su receta a lo que dejó la 026: versión de Python permitida en `recipes.PYTHON` y torch. Si la 034 entra primero, la 026 incluye la receta `pyannote` en su actualización.

## Orden y dependencias

```text
034 → 035 → 036 → 037 → 038 → 039
```

Se ejecutan con `run-specs` en orden numérico. Todo lo que carga pyannote o faster-whisper va con el turno de la GPU (`turno-gpu.md`).
