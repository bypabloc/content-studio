# 010: el vúmetro (LevelMeter) se hace con su pantalla, en el ciclo 7

- **Contexto**: el plan del ciclo 6 lista `LevelMeter.tsx`. Es un componente de UI: en `features/` solo se usan átomos, moléculas y organismos (`ui-components.md`), así que el medidor pide un átomo nuevo con su inventario y su prueba. Su único consumidor es la pantalla Grabar del ciclo 7.
- **Elegida**: `useRecorder` ya entrega `levels` (pico y RMS en dBFS, a 10 Hz, con suelo de -120). El componente y el átomo entran en el ciclo 7, junto con la pantalla que los usa y sus pruebas.
- **Descartadas**: un medidor con `<div>` en `features/` (la etapa `ui-structure` lo rechaza); un átomo sin consumidor (KISS).
- **Cómo revertir**: no aplica, no hay UI que revertir.
- **Cómo comprobarla**: `bunx vitest run tests/unit/src/features/recording/capture` (el nivel sale de los bloques del worklet). En el ciclo 7, el test de `RecordWizard`.
- **Pendiente**: ninguno fuera de la spec; el medidor se cierra en el ciclo 7.
