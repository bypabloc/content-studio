# 008: `LicenseDialog` sigue en la raíz de `shared/components/`

- **Qué**: `LicenseDialog.tsx` no es átomo, molécula ni organismo de D-3, y lo usa `features/narration/NarrationOptions.tsx`. T4 no lo movió.
- **Por qué no se hizo**: la tabla de archivos de la spec no lo asigna a ningún task, y su destino depende de si queda en `shared/` o pasa a `features/narration/`.
- **Cuándo**: T6 (migración de `features/` y `app/`).
- **Quién**: agente.
- **Qué la cierra**: el archivo queda en su lugar definitivo, con su test movido, y `ui-structure` en verde.
