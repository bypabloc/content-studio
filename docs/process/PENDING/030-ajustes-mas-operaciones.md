# 030: Ajustes ofrece solo convertir a MP3

- **Qué**: AC-9 dice «elegir la operación». Ajustes > Integraciones solo ofrece «Convertir a MP3»; normalizar, limpiar silencios y los demás tipos que aceptan archivos no aparecen.
- **Por qué no se hizo**: el formulario de cada tipo ya vive en su sección, y repetirlo en Ajustes no lo pide la spec. Se deja un tipo para cerrar el flujo.
- **Cuándo**: después de publicar 030.
- **Quién**: usuario (decide qué tipos entran).
- **Qué lo cierra**: la decisión del usuario y un e2e por tipo en `tests/e2e/settings/`.
