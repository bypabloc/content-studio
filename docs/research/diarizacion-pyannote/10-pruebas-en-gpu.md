# 10. Pruebas en GPU: VRAM, tiempo, DER, WDER y turnos (spec 039)

- **Fecha**: 2026-11-25. **Equipo**: RTX 4060 Laptop, 8 GB, driver 621.24, Windows 11.
- **Motor**: `pyannote.audio==4.1.1` con `torch==2.11.0+cu128` y `torchaudio==2.11.0+cu128`; modelo `pyannote/speaker-diarization-community-1` a la revisión de la receta. Instalado: 4,91 GB (`size_gb` 5).
- **Corridas**: `uv run studio diarize <clip>` (la CLI toma el turno de la GPU sola); pico de VRAM con `nvidia-smi` cada 2 s. Transcripción y Limpiador por la API (`small`).

## AC-2: VRAM y tiempo por hora de audio

| Clip | Duración | Tiempo | Pico total en la GPU | Pico menos línea base |
| :--- | :--- | :--- | :--- | :--- |
| Montaje repetido de 30 min | 30 min 18 s | 63 s | 3107 MiB | 879 MiB |
| Montaje repetido de 60 min | 60 min 36 s | 122 s | 3328 MiB | 1100 MiB |

La línea base es 2228 MiB, ocupados por otros procesos antes de cada corrida. El aporte de pyannote es de unos 1,1 GB; `vram_gb` queda en 1,5 (redondeado hacia arriba a 0,5). El pico total de 3,3 GB supera los 3 GB del AC-2 por 0,3 GB, porque la GPU ya tenía 2,2 GB en uso. Tiempo: unos 2 min por hora de audio. Los clips de 30 y 60 min repiten el mismo diálogo: miden VRAM y tiempo, no precisión.

## AC-3: DER y WDER de clips propios

| Clip | Hablantes | Duración | DER sin collar | DER con collar de 0,25 s | WDER |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Diálogo de dos voces | 2 | 50,4 s | 10,5 % | 9,2 % | 0,0 % (101 palabras) |
| Diálogo de tres voces | 3 | 72,6 s | 7,7 % | 6,4 % | 0,0 % (123 palabras) |

Los clips son montajes de muestras de voz (`andrea`, `colombia-m`, `alba-mackenna`) con pausas de 0,8 s, no conversaciones reales. La referencia son los instantes de cada montaje (`referencia.json`), no una anotación a mano (ver `docs/process/WARNING/039-referencia-construida.md`). El DER se calcula por cuadros de 10 ms, con la asignación de hablantes que minimiza el error. El WDER usa el hablante de cada palabra de la transcripción, medido en su punto medio. El error del DER en dos voces viene de pausas dentro de un mismo hablante.

## AC-1: mismos turnos en las cuatro entradas

Un mismo clip de dos voces, por la API: diarización (Hablantes), transcripción con hablantes (Transcripción), proyecto de subtítulos desde la transcripción (Subtítulos) y análisis del Limpiador con hablantes.

- Hablantes, Transcripción y Limpiador usan los mismos hablantes (`SPEAKER_00` y `SPEAKER_01`) y los mismos turnos: 4 palabras de 103 caen en pausas de la diarización (entre 0,1 y 0,5 s de un turno al siguiente). Con 0,5 s de tolerancia, no hay discrepancias.
- Subtítulos: 13 cues, ninguno contradice la diarización.
- **Pendiente**: que solo la primera vez se cargue el modelo. Los logs de los trabajos salen vacíos y no lo registran (`docs/process/PENDING/039-carga-una-vez.md`).

## Qué cambió en la receta

- `vram_gb`: 2 → 1,5 (medido).
- `size_gb`: 6 → 5 (medido: 4,91 GB).
- Paso `torch` y `torchaudio` fijado después de `pyannote.audio` (ver el commit `1d6223e`).

