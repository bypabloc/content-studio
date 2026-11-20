# 006: el modo archivo de la CLI comparte `blocks/` y `script.json` entre tomas de una misma carpeta

- **Qué**: con `--output archivo.wav`, la carpeta de la toma es la del `.wav`. Dos tomas en esa carpeta se pisan `blocks/` y `script.json`, igual que ya se pisa el `.json` de metadatos. El servicio de trabajos da una carpeta por toma, así que solo afecta a la CLI usada a mano.
- **Por qué no se hizo**: el AC-2 pide la carpeta del trabajo. Cambiar el modo archivo (una subcarpeta por toma, o rechazar la carpeta compartida) toca la forma de la CLI en `narration/script.py` (`plan()`), que la spec no cambia.
- **Cuándo**: después de publicar, o antes si la 007 o la 009 lanzan la CLI en lote a una misma carpeta.
- **Quién**: agente.
- **Qué la cierra**: decidir la forma en `plan()` y una prueba de que dos tomas en una carpeta no se pisan, o de que la CLI rechaza la carpeta compartida.
