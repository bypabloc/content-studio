# 010: «Grabar» abre el asistente en lugar de la ficha; «Volver a la ficha» queda bloqueado durante una toma

- **Contexto**: `MyVoicesPage` ya cambia entre la lista y la ficha con un estado; la sección no tiene rutas para estas vistas. Los tests RED piden que «Grabar» abra el asistente del perfil y que terminar vuelva a la ficha.
- **Elegida**: un segundo estado (`recording`) en `MyVoicesPage` que reemplaza la ficha mientras se graba. «Volver a la ficha» del asistente se deshabilita mientras hay un micrófono abierto, una toma subiendo o una prueba de sala, para no perder una toma sin aviso. `features/voices` importa `RecordWizard` de `features/recording`, y este importa `useKit` de `features/voices`: el lint de `features/` lo permite.
- **Descartadas**: una ruta nueva (la sección no tiene router para esto); un diálogo a pantalla completa (más código sin ganar nada); salir a mitad de una toma (la perdería sin aviso).
- **Cómo revertir**: quitar el estado `recording` de `MyVoicesPage` y el botón «Grabar» de `ProfileDetail`.
- **Cómo comprobarla**: `cd client && bunx vitest run tests/unit/src/features/voices`.
- **Pendiente**: ninguno.
