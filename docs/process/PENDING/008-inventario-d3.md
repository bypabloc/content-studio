# 008: el inventario de D-3 debe listar los átomos reales

- **Qué**: `atoms/` tiene 26 carpetas: los 24 de D-3 más `UIFieldFrame` y `UIQrCode`, que la tabla de D-3 no lista. T4 suma `UIChartMarker` y `UIChartPlaceholder`.
- **Por qué no se hizo**: el test de inventario (`inventory.test.ts`, AC-1) llega con T8, y ajustar la tabla de D-3 es decisión de la spec.
- **Cuándo**: T8, antes del cierre de la 008.
- **Quién**: agente.
- **Qué la cierra**: la tabla de D-3 lista los átomos reales (o se renombran) y `inventory.test.ts` pasa.
