# 008: revisión visual de los organismos adaptados

- **Qué**: las celdas de `UIDateRangePicker` pasan de `button` nativo a `UIButton` ghost; el asa de `UIFloatingToolbar` pasa a `UIButton`; el título de `UIChartCard` y el de `UIFloatingToolbar` pasan a `UIBox` con rol de encabezado. Los tests comprueban roles y clases, no el dibujo.
- **Por qué no se hizo**: esta sesión no tiene la app abierta en el navegador.
- **Cuándo**: en el e2e de T5 y T6, o antes de la primera versión en `main`.
- **Quién**: agente (con Playwright) y usuario (revisión visual final).
- **Qué la cierra**: capturas en `tmp/e2e/` que muestren las celdas de 40 px, el asa en las cuatro esquinas y la tarjeta de gráfica, sin cambios de tamaño ni de color frente a klinikae.
