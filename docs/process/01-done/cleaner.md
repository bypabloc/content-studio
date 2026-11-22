---
modulo: cleaner
actualizada: 2026-11-21
---

# Limpiador de silencios

## Qué resuelve

Quita los silencios entre palabras de un audio o de un video, con cortes limpios, y deja revisar cada corte antes de renderizar. La transcripción la hace faster-whisper en local.

## Qué hace hoy

- `uv run studio clean <archivos> [--auto]`: analiza cada archivo y propone cortes por huecos entre palabras (huecos de 500 ms o más, margen de 150 ms a cada lado). Con `--auto` renderiza sin revisar.
- Salidas: `clean.wav` (audio, con fundido de 15 ms de entrada y de salida en cada tramo, sin solaparse) o `clean.mp4` (video, con corte exacto en el cuadro y el mismo audio; NVENC p5 cq19, o libx264 crf 18 si no hay NVENC). El informe, el EDL y el XML usan los mismos tiempos que el archivo. Cada análisis deja la transcripción, `cuts.json`, SRT, EDL, XML e informe.
- Sección **Limpiador** de la app: lote con «Analizar» y «Aplicar todos sin revisar»; «Revisar» abre el video o solo el audio con su onda, los cortes como regiones arrastrables, márgenes que replanifican sin GPU, «Escuchar sin cortes», atajos (Espacio, ← y →, D) y «Renderizar».
- Modelo de transcripción: el que se elige en el selector (`select.whisper.model`), large-v3-turbo por defecto (★). La evaluación de narración y el chequeo de tomas usan el mismo servicio: el comando `whisper` ya no se usa.
- Un envío que el servidor rechaza (por ejemplo, un formato que no acepta) muestra su motivo en la sección.

## Dónde vive

- Código: `server/src/content_studio/clean/` (plan de cortes, render, exportaciones y análisis), `server/src/content_studio/transcription/` (servicio de faster-whisper), `server/src/content_studio/api/routes/clean.py` (API de revisión).
- Cliente: `client/src/features/cleaner/` (sección, revisión y cortes), `client/src/shared/components/molecules/UIWhisperModelSelect/` y `client/src/shared/media/useSyncedMedia.ts`.
- Pruebas: e2e en `tests/e2e/cleaner/` (cuatro specs sobre la API grabada en `tests/e2e/_api/clean/`).
- Decisiones: [WARNING 013-plan-y-render](../WARNING/013-plan-y-render.md), [013-transcripcion-cache](../WARNING/013-transcripcion-cache.md), [013-limpiador-lote-y-revision](../WARNING/013-limpiador-lote-y-revision.md), [013-evaluacion-faster-whisper](../WARNING/013-evaluacion-faster-whisper.md) y [013-cuda-windows](../WARNING/013-cuda-windows.md).

## Historial

- 2026-11-21: spec 013 (limpiador y faster-whisper), tareas T1 a T8: plan de cortes, exportaciones, render de audio y de video, transcripción con caché, trabajos y API, sección del cliente y migración de la evaluación a faster-whisper (AC-10).

## Verificación (2026-11-21)

- Gate `test-runner --type=all`: 12 etapas en verde (lint, spelling, validators, unit, typecheck, tdd, client-lint, client-typecheck, client-unit, ui-structure, budget, i18n).
- e2e en desktop-chromium: 36 de 36 pasan, con los cuatro del limpiador.
- Corrida real (video de 232 s, large-v3-turbo): silencios ≥0,8 s = 0; sincronía 3 ms; informe = archivo; VRAM de la transcripción +1,28 GB; sin clics en las uniones; EDL con 42 eventos y XML con 42 clips. Lote de 3 archivos con `--auto` OK.
- Evaluación de narración con `--evaluate` (faster-whisper) en real: transcripción = texto pedido, sin observaciones (AC-10).
- Regiones de la revisión: se dibujan al recibir «ready» (fix 8); posiciones medidas en el DOM con la duración del archivo. Ver [WARNING 013-regiones-duracion-del-analisis](../WARNING/013-regiones-duracion-del-analisis.md).
- Pendiente: escucha del usuario y revisión manual de la UI, en [PENDING 013-escucha-y-revision-manual](../PENDING/013-escucha-y-revision-manual.md).
