# 010: el medidor de nivel es el átomo `UILevelMeter`, no un `LevelMeter` de la pantalla

- **Contexto**: la ficha [010-vumetro-en-ciclo-7](010-vumetro-en-ciclo-7.md) lo dejaba como `LevelMeter.tsx` en la pantalla de grabar. El test RED del 7c-2 lo fija en `shared/components/atoms/UILevelMeter`.
- **Elegida**: un átomo sin textos (el rótulo lo pone quien lo usa, con `label`), sin imports, con `role="meter"`. Las zonas y el aviso de nivel alto llegan por props. Mide el RMS con una marca de pico.
- **Descartadas**: `LevelMeter.tsx` en `features/recording` (una sola pantalla lo usaría y el test ya fija la ruta); una molécula (no compone otros átomos).
- **Cómo revertir**: mover `UILevelMeter/index.tsx` a `features/recording/` y ajustar el import de `RecordControls.tsx` y del test.
- **Cómo comprobarla**: `cd client && bunx vitest run tests/unit/src/shared/components/atoms/UILevelMeter`.
- **Pendiente**: ninguno. Sustituye la ubicación de la ficha 010-vumetro-en-ciclo-7.
