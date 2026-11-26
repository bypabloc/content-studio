---
modulo: transcription
actualizada: 2026-11-25
---

# Transcripción

## Qué resuelve

Transcribe un audio o un video con faster-whisper y muestra el texto. Con «Identificar hablantes», separa el texto por hablante (pyannote, spec 035), lo nombra y le asigna un color.

## Qué hace hoy

- Sección **Transcripción** (grupo «Editar», antes de Limpiador): archivo, modelo, idioma, e «Identificar hablantes» con su número de hablantes (automático, exacto o rango). Sin el motor de hablantes instalado, el interruptor queda apagado y enlaza a Motores.
- Resultado: un bloque por hablante con su nombre y su color. Al pulsar una palabra, el reproductor va a su tiempo. Sin hablantes, un párrafo por segmento.
- Leyenda de hablantes: renombrar y cambiar el color. Cada cambio guarda el mapa entero.
- Exportar texto (TXT, con o sin marcas de tiempo) y «Crear subtítulos», que abre el proyecto en Subtítulos.

## Dónde vive

- Cliente: `client/src/features/transcription/` (sección, formulario y resultado), `client/src/shared/components/molecules/UISpeakerLegend/` y `UISpeakerCountField/`, y `client/src/shared/hooks/useSpeakers.ts`.
- Servidor: `server/src/content_studio/services/transcribe.py` (trabajo `transcribe`), `server/src/content_studio/transcription/transcribe_main.py` (faster-whisper) y `server/src/content_studio/api/routes/speakers.py` (nombres y colores de los hablantes).
- Textos: `server/src/content_studio/messages/{es,en,pt}.json` (claves `transcription.*` y `speakers.*`).
- Pruebas: `tests/e2e/transcription/` (tres pruebas con API grabada en `tests/e2e/_api/transcription/`) y `tests/e2e/app-check/transcription.check.ts`.

## Pendiente

- La corrida real con hablantes en la app instalada: `docs/process/WARNING/verificacion-app-instalada.md`.

## Historial

- 2025-11-25: spec 036 (sección Transcripción con «Identificar hablantes», leyenda editable, texto por bloques, exportar TXT y crear subtítulos).
