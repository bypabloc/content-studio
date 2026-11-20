# 009: «Abrir carpeta» como botón de solo ícono, cuando haya una carpeta que mostrar

- **Qué**: D-5 pide un botón de solo ícono «Abrir carpeta» en Narración y en la cola. Hoy ninguna pantalla lo muestra: la cola oculta los trabajos terminados, y el aviso de «Abrir carpeta» es una acción de texto del toast (`notify.open_folder`).
- **Por qué no se hizo**: D-5 aplica «a lo que existe al ejecutar»; crear el botón sería una función nueva, no un cambio de iconos.
- **Cuándo**: cuando una pantalla muestre la carpeta de salida de un trabajo. El botón será un `UIIconButton` con `icon="open-folder"` y la clave `action.open_folder` en los tres catálogos.
- **Quién**: agente.
- **Qué la cierra**: el botón en la pantalla que lo muestre, con su prueba por rol y nombre, y su tooltip en `tests/e2e/shell/happy-icons-tooltips.e2e.ts`.
